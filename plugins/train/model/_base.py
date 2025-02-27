#!/usr/bin/env python3
"""
Base class for Models. ALL Models should at least inherit from this class.

See :mod:`~plugins.train.model.original` for an annotated example for how to create model plugins.
"""
import logging
import os
import platform
import sys
import time

from collections import OrderedDict
from contextlib import nullcontext

import numpy as np
import tensorflow as tf

from lib.serializer import get_serializer
from lib.model.backup_restore import Backup
from lib.model import losses, optimizers
from lib.model.nn_blocks import set_config as set_nnblock_config
from lib.utils import get_backend, FaceswapError
from plugins.train._config import Config

if get_backend() == "amd":
    from keras import losses as k_losses
    from keras import backend as K
    from keras.layers import Input
    from keras.models import load_model, Model as KModel
else:
    # Ignore linting errors from Tensorflow's thoroughly broken import system
    from tensorflow.keras import losses as k_losses  # pylint:disable=import-error
    from tensorflow.keras import backend as K  # pylint:disable=import-error
    from tensorflow.keras.layers import Input  # pylint:disable=import-error,no-name-in-module
    from tensorflow.keras.models import load_model, Model as KModel  # noqa pylint:disable=import-error,no-name-in-module


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
_CONFIG = None


def KerasModel(inputs, outputs, name):  # pylint:disable=invalid-name
    """ wrapper for :class:`keras.models.Model`.

    There are some minor foibles between Keras 2.2 and the Tensorflow version of Keras, so this
    catches potential issues and fixes prior to returning the requested model.

    All models created within plugins should use this method, and should not call keras directly
    for a model.

    Parameters
    ----------
    inputs: a keras.Input object or list of keras.Input objects.
        The input(s) of the model
    outputs: keras objects
        The output(s) of the model.
    name: str
        The name of the model.

    Returns
    -------
    :class:`keras.models.Model`
        A Keras Model
    """
    if get_backend() == "amd":
        logger.debug("Flattening inputs (%s) and outputs (%s) for AMD", inputs, outputs)
        inputs = np.array(inputs).flatten().tolist()
        outputs = np.array(outputs).flatten().tolist()
        logger.debug("Flattened inputs (%s) and outputs (%s)", inputs, outputs)
    return KModel(inputs, outputs, name=name)


def _get_all_sub_models(model, models=None):
    """ For a given model, return all sub-models that occur (recursively) as children.

    Parameters
    ----------
    model: :class:`keras.models.Model`
        A Keras model to scan for sub models
    models: `None`
        Do not provide this parameter. It is used for recursion

    Returns
    -------
    list
        A list of all :class:`keras.models.Model`s found within the given model. The provided
        model will always be returned in the first position
    """
    if models is None:
        models = [model]
    else:
        models.append(model)
    for layer in model.layers:
        if isinstance(layer, KModel):
            _get_all_sub_models(layer, models=models)
    return models


class ModelBase():
    """ Base class that all model plugins should inherit from.

    Parameters
    ----------
    model_dir: str
        The full path to the model save location
    arguments: :class:`argparse.Namespace`
        The arguments that were passed to the train or convert process as generated from
        Faceswap's command line arguments
    predict: bool, optional
        ``True`` if the model is being loaded for inference, ``False`` if the model is being loaded
        for training. Default: ``False``

    Attributes
    ----------
    input_shape: tuple or list
        A `tuple` of `ints` defining the shape of the faces that the model takes as input. This
        should be overridden by model plugins in their :func:`__init__` function. If the input size
        is the same for both sides of the model, then this can be a single 3 dimensional `tuple`.
        If the inputs have different sizes for `"A"` and `"B"` this should be a `list` of 2 3
        dimensional shape `tuples`, 1 for each side respectively.
    trainer: str
        Currently there is only one trainer available (`"original"`), so at present this attribute
        can be ignored. If/when more trainers are added, then this attribute should be overridden
        with the trainer name that a model requires in the model plugin's
        :func:`__init__` function.
    """
    def __init__(self, model_dir, arguments, predict=False):
        logger.debug("Initializing ModelBase (%s): (model_dir: '%s', arguments: %s, predict: %s)",
                     self.__class__.__name__, model_dir, arguments, predict)

        self.input_shape = None  # Must be set within the plugin after initializing
        self.trainer = "original"  # Override for plugin specific trainer
        self.color_order = "bgr"  # Override for plugin specific image color channel order

        self._args = arguments
        self._is_predict = predict
        self._model = None

        self._configfile = arguments.configfile if hasattr(arguments, "configfile") else None
        self._load_config()

        if self.config["penalized_mask_loss"] and self.config["mask_type"] is None:
            raise FaceswapError("Penalized Mask Loss has been selected but you have not chosen a "
                                "Mask to use. Please select a mask or disable Penalized Mask "
                                "Loss.")

        self._io = _IO(self, model_dir, self._is_predict)
        self._check_multiple_models()

        self._state = State(model_dir,
                            self.name,
                            self._config_changeable_items,
                            False if self._is_predict else self._args.no_logs)
        self._settings = _Settings(self._args,
                                   self.config["mixed_precision"],
                                   self.config["allow_growth"],
                                   self._is_predict)
        self._loss = _Loss()

        logger.debug("Initialized ModelBase (%s)", self.__class__.__name__)

    @property
    def model(self):
        """:class:`Keras.models.Model`: The compiled model for this plugin. """
        return self._model

    @property
    def command_line_arguments(self):
        """ :class:`argparse.Namespace`: The command line arguments passed to the model plugin from
        either the train or convert script """
        return self._args

    @property
    def coverage_ratio(self):
        """ float: The ratio of the training image to crop out and train on as defined in user
        configuration options.

        NB: The coverage ratio is a raw float, but will be applied to integer pixel images.

        To ensure consistent rounding and guaranteed even image size, the calculation for coverage
        should always be: :math:`(original_size * coverage_ratio // 2) * 2`
        """
        return self.config.get("coverage", 62.5) / 100

    @property
    def model_dir(self):
        """str: The full path to the model folder location. """
        return self._io._model_dir  # pylint:disable=protected-access

    @property
    def config(self):
        """ dict: The configuration dictionary for current plugin, as set by the user's
        configuration settings. """
        global _CONFIG  # pylint: disable=global-statement
        if not _CONFIG:
            model_name = self._config_section
            logger.debug("Loading config for: %s", model_name)
            _CONFIG = Config(model_name, configfile=self._configfile).config_dict
        return _CONFIG

    @property
    def name(self):
        """ str: The name of this model based on the plugin name. """
        basename = os.path.basename(sys.modules[self.__module__].__file__)
        return os.path.splitext(basename)[0].lower()

    @property
    def model_name(self):
        """ str: The name of the keras model. Generally this will be the same as :attr:`name`
        but some plugins will override this when they contain multiple architectures """
        return self.name

    @property
    def output_shapes(self):
        """ list: A list of list of shape tuples for the outputs of the model with the batch
        dimension removed. The outer list contains 2 sub-lists (one for each side "a" and "b").
        The inner sub-lists contain the output shapes for that side. """
        shapes = [tuple(K.int_shape(output)[-3:]) for output in self._model.outputs]
        return [shapes[:len(shapes) // 2], shapes[len(shapes) // 2:]]

    @property
    def iterations(self):
        """ int: The total number of iterations that the model has trained. """
        return self._state.iterations

    # Private properties
    @property
    def _config_section(self):
        """ str: The section name for the current plugin for loading configuration options from the
        config file. """
        return ".".join(self.__module__.split(".")[-2:])

    @property
    def _config_changeable_items(self):
        """ dict: The configuration options that can be updated after the model has already been
            created. """
        return Config(self._config_section, configfile=self._configfile).changeable_items

    @property
    def state(self):
        """:class:`State`: The state settings for the current plugin. """
        return self._state

    def _load_config(self):
        """ Load the global config for reference in :attr:`config` and set the faceswap blocks
        configuration options in `lib.model.nn_blocks` """
        global _CONFIG  # pylint: disable=global-statement
        if not _CONFIG:
            model_name = self._config_section
            logger.debug("Loading config for: %s", model_name)
            _CONFIG = Config(model_name, configfile=self._configfile).config_dict

        nn_block_keys = ['icnr_init', 'conv_aware_init', 'reflect_padding']
        set_nnblock_config({key: _CONFIG.pop(key)
                            for key in nn_block_keys})

    def _check_multiple_models(self):
        """ Check whether multiple models exist in the model folder, and that no models exist that
        were trained with a different plugin than the requested plugin.

        Raises
        ------
        FaceswapError
            If multiple model files, or models for a different plugin from that requested exists
            within the model folder
        """
        multiple_models = self._io.multiple_models_in_folder
        if multiple_models is None:
            logger.debug("Contents of model folder are valid")
            return

        if len(multiple_models) == 1:
            msg = (f"You have requested to train with the '{self.name}' plugin, but a model file "
                   f"for the '{multiple_models[0]}' plugin already exists in the folder "
                   f"'{self.model_dir}'.\nPlease select a different model folder.")
        else:
            ptypes = "', '".join(multiple_models)
            msg = (f"There are multiple plugin types ('{ptypes}') stored in the model folder '"
                   f"{self.model_dir}'. This is not supported.\nPlease split the model files into "
                   "their own folders before proceeding")
        raise FaceswapError(msg)

    def build(self):
        """ Build the model and assign to :attr:`model`.

        Within the defined strategy scope, either builds the model from scratch or loads an
        existing model if one exists.

        If running inference, then the model is built only for the required side to perform the
        swap function, otherwise  the model is then compiled with the optimizer and chosen
        loss function(s).

        Finally, a model summary is outputted to the logger at verbose level.
        """
        self._update_legacy_models()
        is_summary = hasattr(self._args, "summary") and self._args.summary
        with self._settings.strategy_scope():
            if self._io.model_exists:
                model = self._io._load()  # pylint:disable=protected-access
                if self._is_predict:
                    inference = _Inference(model, self._args.swap_model)
                    self._model = inference.model
                else:
                    self._model = model
            else:
                self._validate_input_shape()
                inputs = self._get_inputs()
                self._model = self.build_model(inputs)
            if not is_summary and not self._is_predict:
                self._compile_model()
            self._output_summary()

    def _update_legacy_models(self):
        """ Load weights from legacy split models into new unified model, archiving old model files
        to a new folder. """
        if self._legacy_mapping() is None:
            return
        if not all(os.path.isfile(os.path.join(self.model_dir, fname))
                   for fname in self._legacy_mapping()):
            return
        archive_dir = f"{self.model_dir}_TF1_Archived"
        if os.path.exists(archive_dir):
            raise FaceswapError("We need to update your model files for use with Tensorflow 2.x, "
                                "but the archive folder already exists. Please remove the "
                                f"following folder to continue: '{archive_dir}'")

        logger.info("Updating legacy models for Tensorflow 2.x")
        logger.info("Your Tensorflow 1.x models will be archived in the following location: '%s'",
                    archive_dir)
        os.rename(self.model_dir, archive_dir)
        os.mkdir(self.model_dir)
        new_model = self.build_model(self._get_inputs())
        for model_name, layer_name in self._legacy_mapping().items():
            old_model = load_model(os.path.join(archive_dir, model_name), compile=False)
            layer = [layer for layer in new_model.layers if layer.name == layer_name]
            if not layer:
                logger.warning("Skipping legacy weights from '%s'...", model_name)
                continue
            layer = layer[0]
            logger.info("Updating legacy weights from '%s'...", model_name)
            layer.set_weights(old_model.get_weights())
        filename = self._io._filename  # pylint:disable=protected-access
        logger.info("Saving Tensorflow 2.x model to '%s'", filename)
        new_model.save(filename)
        # Penalized Loss and Learn Mask used to be disabled automatically if a mask wasn't
        # selected, so disable it if enabled, but mask_type is None
        if self.config["mask_type"] is None:
            self.config["penalized_mask_loss"] = False
            self.config["learn_mask"] = False
            self.config["eye_multiplier"] = 1
            self.config["mouth_multiplier"] = 1
        self._state.save()

    def _validate_input_shape(self):
        """ Validate that the input shape is either a single shape tuple of 3 dimensions or
        a list of 2 shape tuples of 3 dimensions. """
        assert len(self.input_shape) in (2, 3), "Input shape should either be a single 3 " \
            "dimensional shape tuple for use in both sides of the model, or a list of 2 3 " \
            "dimensional shape tuples for use in the 'A' and 'B' sides of the model"
        if len(self.input_shape) == 2:
            assert [len(shape) == 3 for shape in self.input_shape], "All input shapes should " \
                "have 3 dimensions"

    def _get_inputs(self):
        """ Obtain the standardized inputs for the model.

        The inputs will be returned for the "A" and "B" sides in the shape as defined by
        :attr:`input_shape`.

        Returns
        -------
        list
            A list of :class:`keras.layers.Input` tensors. This will be a list of 2 tensors (one
            for each side) each of shapes :attr:`input_shape`.
        """
        logger.debug("Getting inputs")
        if len(self.input_shape) == 3:
            input_shapes = [self.input_shape, self.input_shape]
        else:
            input_shapes = self.input_shape
        inputs = [Input(shape=shape, name=f"face_in_{side}")
                  for side, shape in zip(("a", "b"), input_shapes)]
        logger.debug("inputs: %s", inputs)
        return inputs

    def build_model(self, inputs):
        """ Override for Model Specific autoencoder builds.

        Parameters
        ----------
        inputs: list
            A list of :class:`keras.layers.Input` tensors. This will be a list of 2 tensors (one
            for each side) each of shapes :attr:`input_shape`.
        """
        raise NotImplementedError

    def _output_summary(self):
        """ Output the summary of the model and all sub-models to the verbose logger. """
        if hasattr(self._args, "summary") and self._args.summary:
            print_fn = None  # Print straight to stdout
        else:
            # print to logger
            print_fn = lambda x: logger.verbose("%s", x)  # noqa
        for idx, model in enumerate(_get_all_sub_models(self._model)):
            if idx == 0:
                parent = model
                continue
            model.summary(line_length=100, print_fn=print_fn)
        parent.summary(line_length=100, print_fn=print_fn)

    def save(self):
        """ Save the model to disk.

        Saves the serialized model, with weights, to the folder location specified when
        initializing the plugin. If loss has dropped on both sides of the model, then
        a backup is taken.
        """
        self._io._save()  # pylint:disable=protected-access

    def snapshot(self):
        """ Creates a snapshot of the model folder to the models parent folder, with the number
        of iterations completed appended to the end of the model name. """
        self._io._snapshot()  # pylint:disable=protected-access

    def _compile_model(self):
        """ Compile the model to include the Optimizer and Loss Function(s). """
        logger.debug("Compiling Model")

        optimizer = _Optimizer(self.config["optimizer"],
                               self.config["learning_rate"],
                               self.config.get("clipnorm", False),
                               10 ** int(self.config["epsilon_exponent"]),
                               self._args).optimizer
        if self._settings.use_mixed_precision:
            optimizer = tf.keras.mixed_precision.LossScaleOptimizer(optimizer)

        if get_backend() == "amd":
            self._rewrite_plaid_outputs()

        weights = _Weights(self)
        weights.load(self._io.model_exists)
        weights.freeze()

        self._loss.configure(self._model)
        self._model.compile(optimizer=optimizer, loss=self._loss.functions)
        self._state.add_session_loss_names(self._loss.names)
        logger.debug("Compiled Model: %s", self._model)

    def _rewrite_plaid_outputs(self):
        """ Rewrite the output names for models using the PlaidML (Keras 2.2.4) backend

        Keras 2.2.4 duplicates model output names if any of the models have multiple outputs
        so we need to rename the outputs so we can successfully map the loss dictionaries.

        This is a bit of a hack, but it does work.
        """
        # TODO Remove this rewrite code if PlaidML updates to a version of Keras where this is
        # no longer necessary
        if len(self._model.output_names) == len(set(self._model.output_names)):
            logger.debug("Output names are unique, not rewriting: %s", self._model.output_names)
            return
        seen = {name: 0 for name in set(self._model.output_names)}
        new_names = []
        for name in self._model.output_names:
            new_names.append(f"{name}_{seen[name]}")
            seen[name] += 1
        logger.debug("Output names rewritten: (old: %s, new: %s)",
                     self._model.output_names, new_names)
        self._model.output_names = new_names

    def _legacy_mapping(self):  # pylint:disable=no-self-use
        """ The mapping of separate model files to single model layers for transferring of legacy
        weights.

        Returns
        -------
        dict or ``None``
            Dictionary of original H5 filenames for legacy models mapped to new layer names or
            ``None`` if the model did not exist in Faceswap prior to Tensorflow 2
        """
        return None

    def add_history(self, loss):
        """ Add the current iteration's loss history to :attr:`_io.history`.

        Called from the trainer after each iteration, for tracking loss drop over time between
        save iterations.

        Parameters
        ----------
        loss: list
            The loss values for the A and B side for the current iteration. This should be the
            collated loss values for each side.
        """
        self._io.history[0].append(loss[0])
        self._io.history[1].append(loss[1])


class _IO():
    """ Model saving and loading functions.

    Handles the loading and saving of the plugin model from disk as well as the model backup and
    snapshot functions.

    Parameters
    ----------
    plugin: :class:`Model`
        The parent plugin class that owns the IO functions.
    model_dir: str
        The full path to the model save location
    is_predict: bool
        ``True`` if the model is being loaded for inference. ``False`` if the model is being loaded
        for training.
    """
    def __init__(self, plugin, model_dir, is_predict):
        self._plugin = plugin
        self._is_predict = is_predict
        self._model_dir = model_dir
        self._history = [[], []]  # Loss histories per save iteration
        self._backup = Backup(self._model_dir, self._plugin.name)

    @property
    def _filename(self):
        """str: The filename for this model."""
        return os.path.join(self._model_dir, f"{self._plugin.name}.h5")

    @property
    def model_exists(self):
        """ bool: ``True`` if a model of the type being loaded exists within the model folder
        location otherwise ``False``.
        """
        return os.path.isfile(self._filename)

    @property
    def history(self):
        """ list: list of loss histories per side for the current save iteration. """
        return self._history

    @property
    def multiple_models_in_folder(self):
        """ :list: or ``None`` If there are multiple model types in the requested folder, or model
        types that don't correspond to the requested plugin type, then returns the list of plugin
        names that exist in the folder, otherwise returns ``None`` """
        plugins = [fname.replace(".h5", "")
                   for fname in os.listdir(self._model_dir)
                   if fname.endswith(".h5")]
        test_names = plugins + [self._plugin.name]
        test = False if not test_names else os.path.commonprefix(test_names) == ""
        retval = None if not test else plugins
        logger.debug("plugin name: %s, plugins: %s, test result: %s, retval: %s",
                     self._plugin.name, plugins, test, retval)
        return retval

    def _load(self):
        """ Loads the model from disk

        If the predict function is to be called and the model cannot be found in the model folder
        then an error is logged and the process exits.

        When loading the model, the plugin model folder is scanned for custom layers which are
        added to Keras' custom objects.

        Returns
        -------
        :class:`keras.models.Model`
            The saved model loaded from disk
        """
        logger.debug("Loading model: %s", self._filename)
        if self._is_predict and not self.model_exists:
            logger.error("Model could not be found in folder '%s'. Exiting", self._model_dir)
            sys.exit(1)

        try:
            model = load_model(self._filename, compile=False)
        except RuntimeError as err:
            if "unable to get link info" in str(err).lower():
                msg = (f"Unable to load the model from '{self._filename}'. This may be a "
                       "temporary error but most likely means that your model has corrupted.\n"
                       "You can try to load the model again but if the problem persists you "
                       "should use the Restore Tool to restore your model from backup.\n"
                       f"Original error: {str(err)}")
                raise FaceswapError(msg) from err
            raise err
        except KeyError as err:
            if "unable to open object" in str(err).lower():
                msg = (f"Unable to load the model from '{self._filename}'. This may be a "
                       "temporary error but most likely means that your model has corrupted.\n"
                       "You can try to load the model again but if the problem persists you "
                       "should use the Restore Tool to restore your model from backup.\n"
                       f"Original error: {str(err)}")
                raise FaceswapError(msg) from err
            raise err

        logger.info("Loaded model from disk: '%s'", self._filename)
        return model

    def _save(self):
        """ Backup and save the model and state file.

        Notes
        -----
        The backup function actually backups the model from the previous save iteration rather than
        the current save iteration. This is not a bug, but protection against long save times, as
        models can get quite large, so renaming the current model file rather than copying it can
        save substantial amount of time.
        """
        logger.debug("Backing up and saving models")
        print("")  # Insert a new line to avoid spamming the same row as loss output
        save_averages = self._get_save_averages()
        if save_averages and self._should_backup(save_averages):
            self._backup.backup_model(self._filename)
            # pylint:disable=protected-access
            self._backup.backup_model(self._plugin.state._filename)

        self._plugin.model.save(self._filename, include_optimizer=False)
        self._plugin.state.save()

        msg = "[Saved models]"
        if save_averages:
            lossmsg = [f"face_{side}: {avg:.5f}"
                       for side, avg in zip(("a", "b"), save_averages)]
            msg += f" - Average loss since last save: {', '.join(lossmsg)}"
        logger.info(msg)

    def _get_save_averages(self):
        """ Return the average loss since the last save iteration and reset historical loss """
        logger.debug("Getting save averages")
        if not all(loss for loss in self._history):
            logger.debug("No loss in history")
            retval = []
        else:
            retval = [sum(loss) / len(loss) for loss in self._history]
            self._history = [[], []]  # Reset historical loss
        logger.debug("Average losses since last save: %s", retval)
        return retval

    def _should_backup(self, save_averages):
        """ Check whether the loss averages for this save iteration is the lowest that has been
        seen.

        This protects against model corruption by only backing up the model if both sides have
        seen a total fall in loss.

        Notes
        -----
        This is by no means a perfect system. If the model corrupts at an iteration close
        to a save iteration, then the averages may still be pushed lower than a previous
        save average, resulting in backing up a corrupted model.

        Parameters
        ----------
        save_averages: list
            The average loss for each side for this save iteration
        """
        backup = True
        for side, loss in zip(("a", "b"), save_averages):
            if not self._plugin.state.lowest_avg_loss.get(side, None):
                logger.debug("Set initial save iteration loss average for '%s': %s", side, loss)
                self._plugin.state.lowest_avg_loss[side] = loss
                continue
            backup = loss < self._plugin.state.lowest_avg_loss[side] if backup else backup

        if backup:  # Update lowest loss values to the state file
            # pylint:disable=unnecessary-comprehension
            old_avgs = {key: val for key, val in self._plugin.state.lowest_avg_loss.items()}
            self._plugin.state.lowest_avg_loss["a"] = save_averages[0]
            self._plugin.state.lowest_avg_loss["b"] = save_averages[1]
            logger.debug("Updated lowest historical save iteration averages from: %s to: %s",
                         old_avgs, self._plugin.state.lowest_avg_loss)

        logger.debug("Should backup: %s", backup)
        return backup

    def _snapshot(self):
        """ Perform a model snapshot.

        Notes
        -----
        Snapshot function is called 1 iteration after the model was saved, so that it is built from
        the latest save, hence iteration being reduced by 1.
        """
        logger.debug("Performing snapshot. Iterations: %s", self._plugin.iterations)
        self._backup.snapshot_models(self._plugin.iterations - 1)
        logger.debug("Performed snapshot")


class _Settings():
    """ Tensorflow core training settings.

    Sets backend tensorflow settings prior to launching the model.

    Tensorflow 2 uses distribution strategies for multi-GPU/system training. These are context
    managers. To enable the code to be more readable, we handle strategies the same way for Nvidia
    and AMD backends. PlaidML does not support strategies, but we need to still create a context
    manager so that we don't need branching logic.

    Parameters
    ----------
    arguments: :class:`argparse.Namespace`
        The arguments that were passed to the train or convert process as generated from
        Faceswap's command line arguments
    mixed_precision: bool
        ``True`` if Mixed Precision training should be used otherwise ``False``
    allow_growth: bool
        ``True`` if the Tensorflow allow_growth parameter should be set otherwise ``False``
    is_predict: bool, optional
        ``True`` if the model is being loaded for inference, ``False`` if the model is being loaded
        for training. Default: ``False``
    """
    def __init__(self, arguments, mixed_precision, allow_growth, is_predict):
        logger.debug("Initializing %s: (arguments: %s, mixed_precision: %s, allow_growth: %s, "
                     "is_predict: %s)", self.__class__.__name__, arguments, mixed_precision,
                     allow_growth, is_predict)
        self._set_tf_settings(allow_growth, arguments.exclude_gpus)

        use_mixed_precision = not is_predict and mixed_precision and get_backend() == "nvidia"
        self._use_mixed_precision = self._set_keras_mixed_precision(use_mixed_precision,
                                                                    bool(arguments.exclude_gpus))

        distributed = False if not hasattr(arguments, "distributed") else arguments.distributed
        self._strategy = self._get_strategy(distributed)
        logger.debug("Initialized %s", self.__class__.__name__)

    @property
    def use_strategy(self):
        """ bool: ``True`` if a distribution strategy is to be used otherwise ``False``. """
        return self._strategy is not None

    @property
    def use_mixed_precision(self):
        """ bool: ``True`` if mixed precision training has been enabled, otherwise ``False``. """
        return self._use_mixed_precision

    @classmethod
    def _set_tf_settings(cls, allow_growth, exclude_devices):
        """ Specify Devices to place operations on and Allow TensorFlow to manage VRAM growth.

        Enables the Tensorflow allow_growth option if requested in the command line arguments

        Parameters
        ----------
        allow_growth: bool
            ``True`` if the Tensorflow allow_growth parameter should be set otherwise ``False``
        exclude_devices: list or ``None``
            List of GPU device indices that should not be made available to Tensorflow. Pass
            ``None`` if all devices should be made available
        """
        if get_backend() == "amd":
            return  # No settings for AMD
        if get_backend() == "cpu":
            logger.verbose("Hiding GPUs from Tensorflow")
            tf.config.set_visible_devices([], "GPU")
            return

        if not exclude_devices and not allow_growth:
            logger.debug("Not setting any specific Tensorflow settings")
            return

        gpus = tf.config.list_physical_devices('GPU')
        if exclude_devices:
            gpus = [gpu for idx, gpu in enumerate(gpus) if idx not in exclude_devices]
            logger.debug("Filtering devices to: %s", gpus)
            tf.config.set_visible_devices(gpus, "GPU")

        if allow_growth:
            logger.debug("Setting Tensorflow 'allow_growth' option")
            for gpu in gpus:
                logger.info("Setting allow growth for GPU: %s", gpu)
                tf.config.experimental.set_memory_growth(gpu, True)
            logger.debug("Set Tensorflow 'allow_growth' option")

    @classmethod
    def _set_keras_mixed_precision(cls, use_mixed_precision, exclude_gpus):
        """ Enable the Keras experimental Mixed Precision API.

        Enables the Keras experimental Mixed Precision API if requested in the user configuration
        file.

        Parameters
        ----------
        use_mixed_precision: bool
            ``True`` if experimental mixed precision support should be enabled for Nvidia GPUs
            otherwise ``False``.
        exclude_gpus: bool
            ``True`` If connected GPUs are being excluded otherwise ``False``.
        """
        logger.debug("use_mixed_precision: %s, exclude_gpus: %s",
                     use_mixed_precision, exclude_gpus)
        if not use_mixed_precision:
            logger.debug("Not enabling 'mixed_precision' (backend: %s, use_mixed_precision: %s)",
                         get_backend(), use_mixed_precision)
            return False
        logger.info("Enabling Mixed Precision Training.")

        policy = tf.keras.mixed_precision.Policy('mixed_float16')
        tf.keras.mixed_precision.set_global_policy(policy)
        logger.debug("Enabled mixed precision. (Compute dtype: %s, variable_dtype: %s)",
                     policy.compute_dtype, policy.variable_dtype)
        return True

    @classmethod
    def _get_strategy(cls, distributed):
        """ If we are running on Nvidia backend and the strategy is not `"default"` then return
        the correct tensorflow distribution strategy, otherwise return ``None``.

        Notes
        -----
        By default Tensorflow defaults mirrored strategy to use the Nvidia NCCL method for
        reductions, however this is only available in Linux, so the method used falls back to
        `Hierarchical Copy All Reduce` if the OS is not Linux.

        Parameters
        ----------
        distributed: bool
            ``True`` if Tensorflow mirrored strategy should be used for multiple GPU training.
            ``False`` if the default strategy should be used.

        Returns
        -------
        :class:`tensorflow.python.distribute.Strategy` or `None`
            The request Tensorflow Strategy if the backend is Nvidia and the strategy is not
            `"Default"` otherwise ``None``
        """
        if get_backend() != "nvidia":
            retval = None
        elif distributed:
            if platform.system().lower() == "linux":
                cross_device_ops = tf.distribute.NcclAllReduce()
            else:
                cross_device_ops = tf.distribute.HierarchicalCopyAllReduce()
            logger.debug("cross_device_ops: %s", cross_device_ops)
            retval = tf.distribute.MirroredStrategy(cross_device_ops=cross_device_ops)
        else:
            retval = tf.distribute.get_strategy()
        logger.debug("Using strategy: %s", retval)
        return retval

    def strategy_scope(self):
        """ Return the strategy scope if we have set a strategy, otherwise return a null
        context.

        Returns
        -------
        :func:`tensorflow.python.distribute.Strategy.scope` or :func:`contextlib.nullcontext`
            The tensorflow strategy scope if a strategy is valid in the current scenario. A null
            context manager if the strategy is not valid in the current scenario
        """
        retval = nullcontext() if self._strategy is None else self._strategy.scope()
        logger.debug("Using strategy scope: %s", retval)
        return retval


class _Weights():
    """ Handling of freezing and loading model weights

    Parameters
    ----------
    plugin: :class:`Model`
        The parent plugin class that owns the IO functions.
    """
    def __init__(self, plugin):
        logger.debug("Initializing %s: (plugin: %s)", self.__class__.__name__, plugin)
        self._model = plugin.model
        self._name = plugin.model_name
        self._do_freeze = plugin._args.freeze_weights
        self._weights_file = self._check_weights_file(plugin._args.load_weights)

        freeze_layers = plugin.config.get("freeze_layers")  # Standardized config for freezing
        load_layers = plugin.config.get("load_layers")  # Standardized config for loading
        self._freeze_layers = freeze_layers if freeze_layers else ["encoder"]  # No plugin config
        self._load_layers = load_layers if load_layers else ["encoder"]  # No plugin config
        logger.debug("Initialized %s", self.__class__.__name__)

    @classmethod
    def _check_weights_file(cls, weights_file):
        """ Validate that we have a valid path to a .h5 file.

        Parameters
        ----------
        weights_file: str
            The full path to a weights file

        Returns
        -------
        str
            The full path to a weights file
        """
        if not weights_file:
            logger.debug("No weights file selected.")
            return None

        msg = ""
        if not os.path.exists(weights_file):
            msg = f"Load weights selected, but the path '{weights_file}' does not exist."
        elif not os.path.splitext(weights_file)[-1].lower() == ".h5":
            msg = (f"Load weights selected, but the path '{weights_file}' is not a valid Keras "
                   f"model (.h5) file.")

        if msg:
            msg += " Please check and try again."
            raise FaceswapError(msg)

        logger.verbose("Using weights file: %s", weights_file)
        return weights_file

    def freeze(self):
        """ If freeze has been selected in the cli arguments, then freeze those models indicated
        in the plugin's configuration. """
        # Blanket unfreeze layers, as checking the value of :attr:`layer.trainable` appears to
        # return ``True`` even when the weights have been frozen
        for layer in _get_all_sub_models(self._model):
            layer.trainable = True

        if not self._do_freeze:
            logger.debug("Freeze weights deselected. Not freezing")
            return

        for layer in _get_all_sub_models(self._model):
            if layer.name in self._freeze_layers:
                logger.info("Freezing weights for '%s' in model '%s'", layer.name, self._name)
                layer.trainable = False
                self._freeze_layers.remove(layer.name)
        if self._freeze_layers:
            logger.warning("The following layers were set to be frozen but do not exist in the "
                           "model: %s", self._freeze_layers)

    def load(self, model_exists):
        """ Load weights for newly created models, or output warning for pre-existing models.

        Parameters
        ----------
        model_exists: bool
            ``True`` if a model pre-exists and is being resumed, ``False`` if this is a new model
        """
        if not self._weights_file:
            logger.debug("No weights file provided. Not loading weights.")
            return
        if model_exists and self._weights_file:
            logger.warning("Ignoring weights file '%s' as this model is resuming.",
                           self._weights_file)
            return

        weights_models = self._get_weights_model()
        all_models = _get_all_sub_models(self._model)

        for model_name in self._load_layers:
            sub_model = next((lyr for lyr in all_models if lyr.name == model_name), None)
            sub_weights = next((lyr for lyr in weights_models if lyr.name == model_name), None)

            if not sub_model or not sub_weights:
                msg = f"Skipping layer {model_name} as not in "
                msg += "current_model." if not sub_model else f"weights '{self._weights_file}.'"
                logger.warning(msg)
                continue

            logger.info("Loading weights for layer '%s'", model_name)
            skipped_ops = 0
            loaded_ops = 0
            for layer in sub_model.layers:
                success = self._load_layer_weights(layer, sub_weights, model_name)
                if success == 0:
                    skipped_ops += 1
                elif success == 1:
                    loaded_ops += 1

        del weights_models

        if loaded_ops == 0:
            raise FaceswapError(f"No weights were succesfully loaded from your weights file: "
                                f"'{self._weights_file}'. Please check and try again.")
        if skipped_ops > 0:
            logger.warning("%s weight(s) were unable to be loaded for your model. This is most "
                           "likely because the weights you are trying to load were trained with "
                           "different settings than you have set for your current model.",
                           skipped_ops)

    def _get_weights_model(self):
        """ Obtain a list of all sub-models contained within the weights model.

        Returns
        -------
        list
            List of all models contained within the .h5 file

        Raises
        ------
        FaceswapError
            In the event of a failure to load the weights, or the weights belonging to a different
            model
        """
        retval = _get_all_sub_models(load_model(self._weights_file, compile=False))
        if not retval:
            raise FaceswapError(f"Error loading weights file {self._weights_file}.")

        if retval[0].name != self._name:
            raise FaceswapError(f"You are attempting to load weights from a '{retval[0].name}' "
                                f"model into a '{self._name}' model. This is not supported.")
        return retval

    def _load_layer_weights(self, layer, sub_weights, model_name):
        """ Load the weights for a single layer.

        Parameters
        ----------
        layer: :class:`keras.layers.Layer`
            The layer to set the weights for
        sub_weights: list
            The list of layers in the weights model to load weights from
        model_name: str
            The name of the current sub-model that is having it's weights loaded

        Returns
        -------
        int
            `-1` if the layer has no weights to load. `0` if weights loading was unsuccessful. `1`
            if weights loading was successful
        """
        old_weights = layer.get_weights()
        if not old_weights:
            logger.debug("Skipping layer without weights: %s", layer.name)
            return -1

        layer_weights = next((lyr for lyr in sub_weights.layers if lyr.name == layer.name), None)
        if not layer_weights:
            logger.warning("The weights file '%s' for layer '%s' does not contain weights for "
                           "'%s'. Skipping", self._weights_file, model_name, layer.name)
            return 0

        new_weights = layer_weights.get_weights()
        if old_weights[0].shape != new_weights[0].shape:
            logger.warning("The weights for layer '%s' are of incompatible shapes. Skipping.",
                           layer.name)
            return 0
        logger.verbose("Setting weights for '%s'", layer.name)
        layer.set_weights(layer_weights.get_weights())
        return 1


class _Optimizer():  # pylint:disable=too-few-public-methods
    """ Obtain the selected optimizer with the appropriate keyword arguments.

    Parameters
    ----------
    optimizer: str
        The selected optimizer name for the plugin
    learning_rate: float
        The selected learning rate to use
    clipnorm: bool
        Whether to clip gradients to avoid exploding/vanishing gradients
    epsilon: float
        The value to use for the epsilon of the optimizer
    arguments: :class:`argparse.Namespace`
        The arguments that were passed to the train or convert process as generated from
        Faceswap's command line arguments
    """
    def __init__(self, optimizer, learning_rate, clipnorm, epsilon, arguments):
        logger.debug("Initializing %s: (optimizer: %s, learning_rate: %s, clipnorm: %s, "
                     "epsilon: %s, arguments: %s)", self.__class__.__name__,
                     optimizer, learning_rate, clipnorm, epsilon, arguments)
        valid_optimizers = {"adabelief": (optimizers.AdaBelief,
                                          dict(beta_1=0.5, beta_2=0.99, epsilon=epsilon)),
                            "adam": (optimizers.Adam,
                                     dict(beta_1=0.5, beta_2=0.99, epsilon=epsilon)),
                            "nadam": (optimizers.Nadam,
                                      dict(beta_1=0.5, beta_2=0.99, epsilon=epsilon)),
                            "rms-prop": (optimizers.RMSprop, dict(epsilon=epsilon))}
        self._optimizer, self._kwargs = valid_optimizers[optimizer]

        self._configure(learning_rate, clipnorm, arguments)
        logger.verbose("Using %s optimizer", optimizer.title())
        logger.debug("Initialized: %s", self.__class__.__name__)

    @property
    def optimizer(self):
        """ :class:`keras.optimizers.Optimizer`: The requested optimizer. """
        return self._optimizer(**self._kwargs)

    def _configure(self, learning_rate, clipnorm, arguments):
        """ Configure the optimizer based on user settings.

        Parameters
        ----------
        learning_rate: float
            The selected learning rate to use
        clipnorm: bool
            Whether to clip gradients to avoid exploding/vanishing gradients
        arguments: :class:`argparse.Namespace`
            The arguments that were passed to the train or convert process as generated from
            Faceswap's command line arguments

        Notes
        -----
        Clip-norm is ballooning VRAM usage, which is not expected behavior and may be a bug in
        Keras/Tensorflow.

        PlaidML has a bug regarding the clip-norm parameter See:
        https://github.com/plaidml/plaidml/issues/228. We workaround by simply not adding this
        parameter for AMD backend users.
        """
        lr_key = "lr" if get_backend() == "amd" else "learning_rate"
        self._kwargs[lr_key] = learning_rate

        if clipnorm and (arguments.distributed or _CONFIG["mixed_precision"]):
            logger.warning("Clipnorm has been selected, but is unsupported when using distributed "
                           "or mixed_precision training, so has been disabled. If you wish to "
                           "enable clipnorm, then you must disable these options.")
            clipnorm = False
        if clipnorm and get_backend() == "amd":
            # TODO add clipnorm in for plaidML when it is fixed upstream. Still not fixed in
            # release 0.7.0.
            logger.warning("Due to a bug in plaidML, clipnorm cannot be used on AMD backends so "
                           "has been disabled")
            clipnorm = False
        if clipnorm:
            self._kwargs["clipnorm"] = 1.0

        logger.debug("optimizer kwargs: %s", self._kwargs)


class _Loss():
    """ Holds loss names and functions for an Autoencoder. """
    def __init__(self):
        logger.debug("Initializing %s", self.__class__.__name__)
        self._loss_dict = dict(mae=k_losses.mean_absolute_error,
                               mse=k_losses.mean_squared_error,
                               logcosh=k_losses.logcosh,
                               smooth_loss=losses.GeneralizedLoss(),
                               l_inf_norm=losses.LInfNorm(),
                               ssim=losses.DSSIMObjective(),
                               ms_ssim=losses.MSSSIMLoss(),
                               gmsd=losses.GMSDLoss(),
                               pixel_gradient_diff=losses.GradientLoss())
        self._uses_l2_reg = ["ssim", "ms_ssim", "gmsd"]
        self._inputs = None
        self._names = []
        self._funcs = {}
        logger.debug("Initialized: %s", self.__class__.__name__)

    @property
    def names(self):
        """ list: The list of loss names for the model. """
        return self._names

    @property
    def functions(self):
        """ dict: The loss functions that apply to each model output. """
        return self._funcs

    @property
    def _config(self):
        """ :dict: The configuration options for this plugin """
        return _CONFIG

    @property
    def _mask_inputs(self):
        """ list: The list of input tensors to the model that contain the mask. Returns ``None``
        if there is no mask input to the model. """
        mask_inputs = [inp for inp in self._inputs if inp.name.startswith("mask")]
        return None if not mask_inputs else mask_inputs

    @property
    def _mask_shapes(self):
        """ list: The list of shape tuples for the mask input tensors for the model. Returns
        ``None`` if there is no mask input. """
        if self._mask_inputs is None:
            return None
        return [K.int_shape(mask_input) for mask_input in self._mask_inputs]

    def configure(self, model):
        """ Configure the loss functions for the given inputs and outputs.

        Parameters
        ----------
        model: :class:`keras.models.Model`
            The model that is to be trained
        """
        self._inputs = model.inputs
        self._set_loss_names(model.outputs)
        self._set_loss_functions(model.output_names)
        self._names.insert(0, "total")

    def _set_loss_names(self, outputs):
        """ Name the losses based on model output.

        This is used for correct naming in the state file, for display purposes only.

        Adds the loss names to :attr:`names`

        Notes
        -----
        TODO Currently there is an issue in Tensorflow that wraps all outputs in an Identity layer
        when running in Eager Execution mode, which means we cannot use the name of the output
        layers to name the losses (https://github.com/tensorflow/tensorflow/issues/32180).
        With this in mind, losses are named based on their shapes

        Parameters
        ----------
        outputs: list
            A list of output tensors from the model plugin
        """
        # TODO Use output names if/when these are fixed upstream
        split_outputs = [outputs[:len(outputs) // 2], outputs[len(outputs) // 2:]]
        for side, side_output in zip(("a", "b"), split_outputs):
            output_names = [output.name for output in side_output]
            output_shapes = [K.int_shape(output)[1:] for output in side_output]
            output_types = ["mask" if shape[-1] == 1 else "face" for shape in output_shapes]
            logger.debug("side: %s, output names: %s, output_shapes: %s, output_types: %s",
                         side, output_names, output_shapes, output_types)
            for idx, name in enumerate(output_types):
                suffix = "" if output_types.count(name) == 1 else f"_{idx}"
                self._names.append(f"{name}_{side}{suffix}")
        logger.debug(self._names)

    def _set_loss_functions(self, output_names):
        """ Set the loss functions and their associated weights.

        Adds the loss functions to the :attr:`functions` dictionary.

        Parameters
        ----------
        output_names: list
            The output names from the model
        """
        mask_channels = self._get_mask_channels()
        face_loss = self._loss_dict[self._config["loss_function"]]

        for name, output_name in zip(self._names, output_names):
            if name.startswith("mask"):
                loss_func = self._loss_dict[self._config["mask_loss_function"]]
            else:
                loss_func = losses.LossWrapper()
                loss_func.add_loss(face_loss, mask_channel=mask_channels[0])
                self._add_l2_regularization_term(loss_func, mask_channels[0])

                channel_idx = 1
                for multiplier in ("eye_multiplier", "mouth_multiplier"):
                    mask_channel = mask_channels[channel_idx]
                    if self._config[multiplier] > 1:
                        loss_func.add_loss(face_loss,
                                           weight=self._config[multiplier] * 1.0,
                                           mask_channel=mask_channel)
                        self._add_l2_regularization_term(loss_func, mask_channel)
                    channel_idx += 1

            logger.debug("%s: (output_name: '%s', function: %s)", name, output_name, loss_func)
            self._funcs[output_name] = loss_func
        logger.debug("functions: %s", self._funcs)

    def _add_l2_regularization_term(self, loss_wrapper, mask_channel):
        """ Check if an L2 Regularization term should be added and add to the loss function
        wrapper.

        Parameters
        ----------
        loss_wrapper: :class:`lib.model.losses.LossWrapper`
            The wrapper loss function that holds the face losses
        mask_channel: int
            The channel that holds the mask in `y_true`, if a mask is used for the loss.
            `-1` if the input is not masked
        """
        if self._config["loss_function"] in self._uses_l2_reg and self._config["l2_reg_term"] > 0:
            logger.debug("Adding L2 Regularization for Structural Loss")
            loss_wrapper.add_loss(self._loss_dict["mse"],
                                  weight=self._config["l2_reg_term"] / 100.0,
                                  mask_channel=mask_channel)

    def _get_mask_channels(self):
        """ Obtain the channels from the face targets that the masks reside in from the training
        data generator.

        Returns
        -------
        list:
            A list of channel indices that contain the mask for the corresponding config item
        """
        eye_multiplier = self._config["eye_multiplier"]
        mouth_multiplier = self._config["mouth_multiplier"]
        if not self._config["penalized_mask_loss"] and (eye_multiplier > 1 or
                                                        mouth_multiplier > 1):
            logger.warning("You have selected eye/mouth loss multipliers greater than 1x, but "
                           "Penalized Mask Loss is disabled. Disabling all multipliers.")
            eye_multiplier = 1
            mouth_multiplier = 1
        uses_masks = (self._config["penalized_mask_loss"],
                      eye_multiplier > 1,
                      mouth_multiplier > 1)
        mask_channels = [-1 for _ in range(len(uses_masks))]
        current_channel = 3
        for idx, mask_required in enumerate(uses_masks):
            if mask_required:
                mask_channels[idx] = current_channel
                current_channel += 1
        logger.debug("uses_masks: %s, mask_channels: %s", uses_masks, mask_channels)
        return mask_channels


class State():
    """ Holds state information relating to the plugin's saved model.

    Parameters
    ----------
    model_dir: str
        The full path to the model save location
    model_name: str
        The name of the model plugin
    config_changeable_items: dict
        Configuration options that can be altered when resuming a model, and their current values
    no_logs: bool
        ``True`` if Tensorboard logs should not be generated, otherwise ``False``
    """
    def __init__(self, model_dir, model_name, config_changeable_items, no_logs):
        logger.debug("Initializing %s: (model_dir: '%s', model_name: '%s', "
                     "config_changeable_items: '%s', no_logs: %s", self.__class__.__name__,
                     model_dir, model_name, config_changeable_items, no_logs)
        self._serializer = get_serializer("json")
        filename = f"{model_name}_state.{self._serializer.file_extension}"
        self._filename = os.path.join(model_dir, filename)
        self._name = model_name
        self._iterations = 0
        self._sessions = {}
        self._lowest_avg_loss = {}
        self._config = {}
        self._load(config_changeable_items)
        self._session_id = self._new_session_id()
        self._create_new_session(no_logs, config_changeable_items)
        logger.debug("Initialized %s:", self.__class__.__name__)

    @property
    def loss_names(self):
        """ list: The loss names for the current session """
        return self._sessions[self._session_id]["loss_names"]

    @property
    def current_session(self):
        """ dict: The state dictionary for the current :attr:`session_id`. """
        return self._sessions[self._session_id]

    @property
    def iterations(self):
        """ int: The total number of iterations that the model has trained. """
        return self._iterations

    @property
    def lowest_avg_loss(self):
        """dict: The lowest average save interval loss seen for each side. """
        return self._lowest_avg_loss

    @property
    def session_id(self):
        """ int: The current training session id. """
        return self._session_id

    def _new_session_id(self):
        """ Generate a new session id. Returns 1 if this is a new model, or the last session id + 1
        if it is a pre-existing model.

        Returns
        -------
        int
            The newly generated session id
        """
        if not self._sessions:
            session_id = 1
        else:
            session_id = max(int(key) for key in self._sessions.keys()) + 1
        logger.debug(session_id)
        return session_id

    def _create_new_session(self, no_logs, config_changeable_items):
        """ Initialize a new session, creating the dictionary entry for the session in
        :attr:`_sessions`.

        Parameters
        ----------
        no_logs: bool
            ``True`` if Tensorboard logs should not be generated, otherwise ``False``
        config_changeable_items: dict
            Configuration options that can be altered when resuming a model, and their current
            values
        """
        logger.debug("Creating new session. id: %s", self._session_id)
        self._sessions[self._session_id] = dict(timestamp=time.time(),
                                                no_logs=no_logs,
                                                loss_names=[],
                                                batchsize=0,
                                                iterations=0,
                                                config=config_changeable_items)

    def add_session_loss_names(self, loss_names):
        """ Add the session loss names to the sessions dictionary.

        The loss names are used for Tensorboard logging

        Parameters
        ----------
        loss_names: list
            The list of loss names for this session.
        """
        logger.debug("Adding session loss_names: %s", loss_names)
        self._sessions[self._session_id]["loss_names"] = loss_names

    def add_session_batchsize(self, batch_size):
        """ Add the session batch size to the sessions dictionary.

        Parameters
        ----------
        batch_size: int
            The batch size for the current training session
        """
        logger.debug("Adding session batch size: %s", batch_size)
        self._sessions[self._session_id]["batchsize"] = batch_size

    def increment_iterations(self):
        """ Increment :attr:`iterations` and session iterations by 1. """
        self._iterations += 1
        self._sessions[self._session_id]["iterations"] += 1

    def _load(self, config_changeable_items):
        """ Load a state file and set the serialized values to the class instance.

        Updates the model's config with the values stored in the state file.

        Parameters
        ----------
        config_changeable_items: dict
            Configuration options that can be altered when resuming a model, and their current
            values
        """
        logger.debug("Loading State")
        if not os.path.exists(self._filename):
            logger.info("No existing state file found. Generating.")
            return
        state = self._serializer.load(self._filename)
        self._name = state.get("name", self._name)
        self._sessions = state.get("sessions", {})
        self._lowest_avg_loss = state.get("lowest_avg_loss", {})
        self._iterations = state.get("iterations", 0)
        self._config = state.get("config", {})
        logger.debug("Loaded state: %s", state)
        self._replace_config(config_changeable_items)

    def save(self):
        """ Save the state values to the serialized state file. """
        logger.debug("Saving State")
        state = {"name": self._name,
                 "sessions": self._sessions,
                 "lowest_avg_loss": self._lowest_avg_loss,
                 "iterations": self._iterations,
                 "config": _CONFIG}
        self._serializer.save(self._filename, state)
        logger.debug("Saved State")

    def _replace_config(self, config_changeable_items):
        """ Replace the loaded config with the one contained within the state file.

        Check for any `fixed`=``False`` parameter changes and log info changes.

        Update any legacy config items to their current versions.

        Parameters
        ----------
        config_changeable_items: dict
            Configuration options that can be altered when resuming a model, and their current
            values
        """
        global _CONFIG  # pylint: disable=global-statement
        legacy_update = self._update_legacy_config()
        # Add any new items to state config for legacy purposes and set sensible defaults for
        # any values that may have been changed in the config file which could be detrimental.
        legacy_defaults = dict(centering="legacy",
                               mask_loss_function="mse",
                               l2_reg_term=100,
                               optimizer="adam",
                               mixed_precision=False)
        for key, val in _CONFIG.items():
            if key not in self._config.keys():
                setting = legacy_defaults.get(key, val)
                logger.info("Adding new config item to state file: '%s': '%s'", key, setting)
                self._config[key] = setting
        self._update_changed_config_items(config_changeable_items)
        logger.debug("Replacing config. Old config: %s", _CONFIG)
        _CONFIG = self._config
        if legacy_update:
            self.save()
        logger.debug("Replaced config. New config: %s", _CONFIG)
        logger.info("Using configuration saved in state file")

    def _update_legacy_config(self):
        """ Legacy updates for new config additions.

        When new config items are added to the Faceswap code, existing model state files need to be
        updated to handle these new items.

        Current existing legacy update items:

            * loss - If old `dssim_loss` is ``true`` set new `loss_function` to `ssim` otherwise
            set it to `mae`. Remove old `dssim_loss` item

            * masks - If `learn_mask` does not exist then it is set to ``True`` if `mask_type` is
            not ``None`` otherwise it is set to ``False``.

            * masks type - Replace removed masks 'dfl_full' and 'facehull' with `components` mask

        Returns
        -------
        bool
            ``True`` if legacy items exist and state file has been updated, otherwise ``False``
        """
        logger.debug("Checking for legacy state file update")
        priors = ["dssim_loss", "mask_type", "mask_type"]
        new_items = ["loss_function", "learn_mask", "mask_type"]
        updated = False
        for old, new in zip(priors, new_items):
            if old not in self._config:
                logger.debug("Legacy item '%s' not in config. Skipping update", old)
                continue

            # dssim_loss > loss_function
            if old == "dssim_loss":
                self._config[new] = "ssim" if self._config[old] else "mae"
                del self._config[old]
                updated = True
                logger.info("Updated config from legacy dssim format. New config loss "
                            "function: '%s'", self._config[new])
                continue

            # Add learn mask option and set to True if model has "penalized_mask_loss" specified
            if old == "mask_type" and new == "learn_mask" and new not in self._config:
                self._config[new] = self._config["mask_type"] is not None
                updated = True
                logger.info("Added new 'learn_mask' config item for this model. Value set to: %s",
                            self._config[new])
                continue

            # Replace removed masks with most similar equivalent
            if old == "mask_type" and new == "mask_type" and self._config[old] in ("facehull",
                                                                                   "dfl_full"):
                old_mask = self._config[old]
                self._config[new] = "components"
                updated = True
                logger.info("Updated 'mask_type' from '%s' to '%s' for this model",
                            old_mask, self._config[new])

        logger.debug("State file updated for legacy config: %s", updated)
        return updated

    def _update_changed_config_items(self, config_changeable_items):
        """ Update any parameters which are not fixed and have been changed.

        Parameters
        ----------
        config_changeable_items: dict
            Configuration options that can be altered when resuming a model, and their current
            values
        """
        if not config_changeable_items:
            logger.debug("No changeable parameters have been updated")
            return
        for key, val in config_changeable_items.items():
            old_val = self._config[key]
            if old_val == val:
                continue
            self._config[key] = val
            logger.info("Config item: '%s' has been updated from '%s' to '%s'", key, old_val, val)


class _Inference():  # pylint:disable=too-few-public-methods
    """ Calculates required layers and compiles a saved model for inference.

    Parameters
    ----------
    saved_model: :class:`keras.models.Model`
        The saved trained Faceswap model
    switch_sides: bool
        ``True`` if the swap should be performed "B" > "A" ``False`` if the swap should be
        "A" > "B"
    """
    def __init__(self, saved_model, switch_sides):
        logger.debug("Initializing: %s (saved_model: %s, switch_sides: %s)",
                     self.__class__.__name__, saved_model, switch_sides)
        self._config = saved_model.get_config()

        self._input_idx = 1 if switch_sides else 0
        self._output_idx = 0 if switch_sides else 1

        self._input_names = [inp[0] for inp in self._config["input_layers"]]
        self._model = self._make_inference_model(saved_model)
        logger.debug("Initialized: %s", self.__class__.__name__)

    @property
    def model(self):
        """ :class:`keras.models.Model`: The Faceswap model, compiled for inference. """
        return self._model

    def _get_nodes(self, nodes):
        """ Given in input list of nodes from a :attr:`keras.models.Model.get_config` dictionary,
        filters the layer name(s) and output index of the node, splitting to the correct output
        index in the event of multiple inputs.

        Parameters
        ----------
        nodes: list
            A node entry from the :attr:`keras.models.Model.get_config` dictionary

        Returns
        -------
        list
            The (node name, output index) for each node passed in
        """
        nodes = np.array(nodes, dtype="object")[..., :3]
        num_layers = nodes.shape[0]
        nodes = nodes[self._output_idx] if num_layers == 2 else nodes[0]
        retval = [(node[0], node[2]) for node in nodes]
        return retval

    def _make_inference_model(self, saved_model):
        """ Extract the sub-models from the saved model that are required for inference.

        Parameters
        ----------
        saved_model: :class:`keras.models.Model`
            The saved trained Faceswap model

        Returns
        -------
        :class:`keras.models.Model`
            The model compiled for inference
        """
        logger.debug("Compiling inference model. saved_model: %s", saved_model)
        struct = self._get_filtered_structure()
        model_inputs = self._get_inputs(saved_model.inputs)
        compiled_layers = {}
        for layer in saved_model.layers:
            if layer.name not in struct:
                logger.debug("Skipping unused layer: '%s'", layer.name)
                continue
            inbound = struct[layer.name]
            logger.debug("Processing layer '%s': (layer: %s, inbound_nodes: %s)",
                         layer.name, layer, inbound)
            if not inbound:
                model = model_inputs
                logger.debug("Adding model inputs %s: %s", layer.name, model)
            else:
                layer_inputs = []
                for inp in inbound:
                    inbound_layer = compiled_layers[inp[0]]
                    if isinstance(inbound_layer, list) and len(inbound_layer) > 1:
                        # Multi output inputs
                        inbound_output_idx = inp[1]
                        next_input = inbound_layer[inbound_output_idx]
                        logger.debug("Selecting output index %s from multi output inbound layer: "
                                     "%s (using: %s)", inbound_output_idx, inbound_layer,
                                     next_input)
                    else:
                        next_input = inbound_layer

                    if get_backend() == "amd" and isinstance(next_input, list):
                        # tensorflow.keras and keras 2.2 behave differently for layer inputs
                        layer_inputs.extend(next_input)
                    else:
                        layer_inputs.append(next_input)

                logger.debug("Compiling layer '%s': layer inputs: %s", layer.name, layer_inputs)
                model = layer(layer_inputs)
            compiled_layers[layer.name] = model
            retval = KerasModel(model_inputs, model, name=f"{saved_model.name}_inference")
        logger.debug("Compiled inference model '%s': %s", retval.name, retval)
        return retval

    def _get_filtered_structure(self):
        """ Obtain the structure of the inference model.

        This parses the model config (in reverse) to obtain the required layers for an inference
        model.

        Returns
        -------
        :class:`collections.OrderedDict`
            The layer name as key with the input name and output index as value.
        """
        # Filter output layer
        out = np.array(self._config["output_layers"], dtype="object")
        if out.ndim == 2:
            out = np.expand_dims(out, axis=1)  # Needs to be expanded for _get_nodes
        outputs = self._get_nodes(out)

        # Iterate backwards from the required output to get the reversed model structure
        current_layers = [outputs[0]]
        next_layers = []
        struct = OrderedDict()
        drop_input = self._input_names[abs(self._input_idx - 1)]
        switch_input = self._input_names[self._input_idx]
        while True:
            layer_info = current_layers.pop(0)
            current_layer = next(lyr for lyr in self._config["layers"]
                                 if lyr["name"] == layer_info[0])
            inbound = current_layer["inbound_nodes"]

            if not inbound:
                break

            inbound_info = self._get_nodes(inbound)

            if any(inb[0] == drop_input for inb in inbound_info):  # Switch inputs
                inbound_info = [(switch_input if inb[0] == drop_input else inb[0], inb[1])
                                for inb in inbound_info]
            struct[layer_info[0]] = inbound_info
            next_layers.extend(inbound_info)

            if not current_layers:
                current_layers = next_layers
                next_layers = []

        struct[switch_input] = []  # Add the input layer
        logger.debug("Model structure: %s", struct)
        return struct

    def _get_inputs(self, inputs):
        """ Obtain the inputs for the requested swap direction.

        Parameters
        ----------
        inputs: list
            The full list of input tensors to the saved faceswap training model

        Returns
        -------
        list
            List of input tensors to feed the model for the requested swap direction
        """
        input_split = len(inputs) // 2
        start_idx = input_split * self._input_idx
        retval = inputs[start_idx: start_idx + input_split]
        logger.debug("model inputs: %s, input_split: %s, start_idx: %s, inference_inputs: %s",
                     inputs, input_split, start_idx, retval)
        return retval
