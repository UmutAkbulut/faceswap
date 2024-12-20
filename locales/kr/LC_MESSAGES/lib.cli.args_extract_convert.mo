Þ    2      ¬  C   <      H  u  I     ¿  <   Ä  ±     9   ³  `  í  Ä   N  f   	     z	  w   	  t   
  Ý   w
     U  .  f  þ         µ     [   Ñ     -     ­  c   I    ­  8  Ç       )  	  B   3     v  Ë   ~  M  J  L    ¢  å  Ì   "    U#  ñ  Ý*  Ä  Ï,    0     ¢3  w   *4  C   ¢4  F   æ4  N   -5  B   |5     ¿5  ¶  A6  ¢  ø7  ¢   9  m   >:     ¬:     ³:    ¼:  °  Û;  	   =  V   =  Þ   í=  ?   Ì>  µ  ?    Â@     ×A     ^B  ¦   lB     C    £C     «D  ]  ¼D  D  F    _G  Ñ   øH  e   ÊI  µ   0J  §   æJ  l   K  N  ûK  y  JM  ?  ÄN  m  P  =   rQ     °Q  æ   ÀQ  Ì  §R  ¯  t[    $]  ï   ­`  	  a  7  µj    íl  B  |q  ¼   ¿t     |u  _   v  d   hv  [   Ív  I   )w     sw  )  x  Î  6z  Ä   |  |   Ê|     G}     N}     $         (   &                      1      ,            /       !   +                 '       
      	   "                                                   %      *   0       2   -                          #             )   .          Automatically save the alignments file after a set amount of frames. By default the alignments file is only saved at the end of the extraction process. NB: If extracting in 2 passes then the alignments file will only start to be saved out during the second pass. WARNING: Don't interrupt the script when writing the file because it might get corrupted. Set to 0 to turn off Data Disable multiprocessing. Slower but less resource intensive. Don't run extraction in parallel. Will run each part of the extraction process separately (one after the other) rather than all at the same time. Useful if VRAM is at a premium. Draw landmarks on the ouput faces for debugging purposes. Enable On-The-Fly Conversion. NOT recommended. You should generate a clean alignments file for your destination video. However, if you wish you can generate the alignments on-the-fly by enabling this option. This will use an inferior extraction pipeline and will lead to substandard results. If an alignments file is found, this option will be ignored. Extract every 'nth' frame. This option will skip frames when extracting faces. For example a value of 1 will extract faces from every frame, a value of 10 will extract faces from every 10th frame. Extract faces from image or video sources.
Extraction plugins can be configured in the 'Settings' Menu Face Processing Filters out faces detected below this size. Length, in pixels across the diagonal of the bounding box. Set to 0 for off For use with the optional nfilter/filter files. Threshold for positive face recognition. Higher values are stricter. For use with the optional nfilter/filter files. Threshold for positive face recognition. Lower values are stricter. NB: Using face filter will significantly decrease extraction speed and its accuracy cannot be guaranteed. Frame Processing Frame ranges to apply transfer to e.g. For frames 10 to 50 and 90 to 100 use --frame-ranges 10-50 90-100. Frames falling outside of the selected range will be discarded unless '-k' (--keep-unchanged) is selected. NB: If you are converting from images, then the filenames must end with the frame-number! If a face isn't found, rotate the images to try to find a face. Can find more faces at the cost of extraction speed. Pass in a single number to use increments of that size up to 360, or pass in a list of numbers to enumerate exactly what angles to check. If you have not cleansed your alignments file, then you can filter out faces by defining a folder here that contains the faces extracted from your input files/video. If this folder is defined, then only faces that exist within your alignments file and also exist within the specified folder will be converted. Leaving this blank will convert all faces that exist within the alignments file. Input directory or video. Either a directory containing the image files you wish to process or path to a video file. NB: This should be the source video/frames NOT the source faces. Model directory. The directory containing the trained model you wish to use for conversion. Obtain and store face identity encodings from VGGFace2. Slows down extract a little, but will save time if using 'sort by face' Only required if converting from images to video. Provide The original video that the source frames were extracted from (for extracting the fps and audio). Optional path to an alignments file. Leave blank if the alignments file is at the default location. Optionally filter out people who you do not wish to extract by passing in images of those people. Should be a small variety of images at different angles and in different conditions. A folder containing the required images or multiple image files, space separated, can be selected. Optionally filter out people who you do not wish to process by passing in an image of that person. Should be a front portrait with a single person in the image. Multiple images can be added space separated. NB: Using face filter will significantly decrease extraction speed and its accuracy cannot be guaranteed. Optionally select people you wish to extract by passing in images of that person. Should be a small variety of images at different angles and in different conditions A folder containing the required images or multiple image files, space separated, can be selected. Optionally select people you wish to process by passing in an image of that person. Should be a front portrait with a single person in the image. Multiple images can be added space separated. NB: Using face filter will significantly decrease extraction speed and its accuracy cannot be guaranteed. Output directory. This is where the converted files will be saved. Plugins Re-feed the initially found aligned face through the aligner. Can help produce better alignments for faces that are rotated beyond 45 degrees in the frame or are at extreme angles. Slows down extraction. R|Additional Masker(s) to use. The masks generated here will all take up GPU RAM. You can select none, one or multiple masks, but the extraction may take longer the more you select. NB: The Extended and Components (landmark based) masks are automatically generated on extraction.
L|bisenet-fp: Relatively lightweight NN based mask that provides more refined control over the area to be masked including full head masking (configurable in mask settings).
L|custom: A dummy mask that fills the mask area with all 1s or 0s (configurable in settings). This is only required if you intend to manually edit the custom masks yourself in the manual tool. This mask does not use the GPU so will not use any additional VRAM.
L|vgg-clear: Mask designed to provide smart segmentation of mostly frontal faces clear of obstructions. Profile faces and obstructions may result in sub-par performance.
L|vgg-obstructed: Mask designed to provide smart segmentation of mostly frontal faces. The mask model has been specifically trained to recognize some facial obstructions (hands and eyeglasses). Profile faces may result in sub-par performance.
L|unet-dfl: Mask designed to provide smart segmentation of mostly frontal faces. The mask model has been trained by community members and will need testing for further description. Profile faces may result in sub-par performance.
The auto generated masks are as follows:
L|components: Mask designed to provide facial segmentation based on the positioning of landmark locations. A convex hull is constructed around the exterior of the landmarks to create a mask.
L|extended: Mask designed to provide facial segmentation based on the positioning of landmark locations. A convex hull is constructed around the exterior of the landmarks and the mask is extended upwards onto the forehead.
(eg: `-M unet-dfl vgg-clear`, `--masker vgg-obstructed`) R|Aligner to use.
L|cv2-dnn: A CPU only landmark detector. Faster, less resource intensive, but less accurate. Only use this if not using a GPU and time is important.
L|fan: Best aligner. Fast on GPU, slow on CPU.
L|external: Import 68 point 2D landmarks or an aligned bounding box from a json file. (configurable in Align settings) R|Detector to use. Some of these have configurable settings in '/config/extract.ini' or 'Settings > Configure Extract 'Plugins':
L|cv2-dnn: A CPU only extractor which is the least reliable and least resource intensive. Use this if not using a GPU and time is important.
L|mtcnn: Good detector. Fast on CPU, faster on GPU. Uses fewer resources than other GPU detectors but can often return more false positives.
L|s3fd: Best detector. Slow on CPU, faster on GPU. Can detect more faces and fewer false positives than other GPU detectors, but is a lot more resource intensive.
L|external: Import a face detection bounding box from a json file. (configurable in Detect settings) R|If selected then the input_dir should be a parent folder containing multiple videos and/or folders of images you wish to extract from. The faces will be output to separate sub-folders in the output_dir. R|Masker to use. NB: The mask you require must exist within the alignments file. You can add additional masks with the Mask Tool.
L|none: Don't use a mask.
L|bisenet-fp_face: Relatively lightweight NN based mask that provides more refined control over the area to be masked (configurable in mask settings). Use this version of bisenet-fp if your model is trained with 'face' or 'legacy' centering.
L|bisenet-fp_head: Relatively lightweight NN based mask that provides more refined control over the area to be masked (configurable in mask settings). Use this version of bisenet-fp if your model is trained with 'head' centering.
L|custom_face: Custom user created, face centered mask.
L|custom_head: Custom user created, head centered mask.
L|components: Mask designed to provide facial segmentation based on the positioning of landmark locations. A convex hull is constructed around the exterior of the landmarks to create a mask.
L|extended: Mask designed to provide facial segmentation based on the positioning of landmark locations. A convex hull is constructed around the exterior of the landmarks and the mask is extended upwards onto the forehead.
L|vgg-clear: Mask designed to provide smart segmentation of mostly frontal faces clear of obstructions. Profile faces and obstructions may result in sub-par performance.
L|vgg-obstructed: Mask designed to provide smart segmentation of mostly frontal faces. The mask model has been specifically trained to recognize some facial obstructions (hands and eyeglasses). Profile faces may result in sub-par performance.
L|unet-dfl: Mask designed to provide smart segmentation of mostly frontal faces. The mask model has been trained by community members and will need testing for further description. Profile faces may result in sub-par performance.
L|predicted: If the 'Learn Mask' option was enabled during training, this will use the mask that was created by the trained model. R|Performing normalization can help the aligner better align faces with difficult lighting conditions at an extraction speed cost. Different methods will yield different results on different sets. NB: This does not impact the output face, just the input to the aligner.
L|none: Don't perform normalization on the face.
L|clahe: Perform Contrast Limited Adaptive Histogram Equalization on the face.
L|hist: Equalize the histograms on the RGB channels.
L|mean: Normalize the face colors to the mean. R|Performs color adjustment to the swapped face. Some of these options have configurable settings in '/config/convert.ini' or 'Settings > Configure Convert Plugins':
L|avg-color: Adjust the mean of each color channel in the swapped reconstruction to equal the mean of the masked area in the original image.
L|color-transfer: Transfers the color distribution from the source to the target image using the mean and standard deviations of the L*a*b* color space.
L|manual-balance: Manually adjust the balance of the image in a variety of color spaces. Best used with the Preview tool to set correct values.
L|match-hist: Adjust the histogram of each color channel in the swapped reconstruction to equal the histogram of the masked area in the original image.
L|seamless-clone: Use cv2's seamless clone function to remove extreme gradients at the mask seam by smoothing colors. Generally does not give very satisfactory results.
L|none: Don't perform color adjustment. R|The plugin to use to output the converted images. The writers are configurable in '/config/convert.ini' or 'Settings > Configure Convert Plugins:'
L|ffmpeg: [video] Writes out the convert straight to video. When the input is a series of images then the '-ref' (--reference-video) parameter must be set.
L|gif: [animated image] Create an animated gif.
L|opencv: [images] The fastest image writer, but less options and formats than other plugins.
L|patch: [images] Outputs the raw swapped face patch, along with the transformation matrix required to re-insert the face back into the original frame. Use this option if you wish to post-process and composite the final face within external tools.
L|pillow: [images] Slower than opencv, but has more options and supports more formats. Scale the final output frames by this amount. 100%% will output the frames at source dimensions. 50%% at half size 200%% at double size Scale the swapped face by this percentage. Positive values will enlarge the face, Negative values will shrink the face. Skip frames that already have detected faces in the alignments file Skip saving the detected faces to disk. Just create an alignments file Skips frames that have already been extracted and exist in the alignments file Swap the model. Instead converting from of A -> B, converts B -> A Swap the original faces in a source video/images to your final faces.
Conversion plugins can be configured in the 'Settings' Menu The maximum number of parallel processes for performing conversion. Converting images is system RAM heavy so it is possible to run out of memory if you have a lot of processes and not enough RAM to accommodate them all. Setting this to 0 will use the maximum available. No matter what you set this to, it will never attempt to use more processes than are available on your system. If singleprocess is enabled this setting will be ignored. The number of times to re-feed the detected face into the aligner. Each time the face is re-fed into the aligner the bounding box is adjusted by a small amount. The final landmarks are then averaged from each iteration. Helps to remove 'micro-jitter' but at the cost of slower extraction speed. The more times the face is re-fed into the aligner, the less micro-jitter should occur but the longer extraction will take. The output size of extracted faces. Make sure that the model you intend to train supports your required size. This will only need to be changed for hi-res models. When used with --frame-ranges outputs the unchanged frames that are not processed instead of discarding them. output settings Project-Id-Version: 
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2024-04-12 12:00+0100
Last-Translator: 
Language-Team: 
Language: ko_KR
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=1; plural=0;
X-Generator: Poedit 3.4.2
 íë ì ìê° ì¤ì ë í alignments íì¼ì ìëì¼ë¡ ì ì¥í©ëë¤. ê¸°ë³¸ì ì¼ë¡ alignments íì¼ì ì¶ì¶ íë¡ì¸ì¤ê° ëë  ëë§ ì ì¥ë©ëë¤. NB: 2ë²ì§¸ ì¶ì¶ìì ì±ê³µíë©´ ë ë²ì§¸ ì¶ì¶ ì¤ìë§ alignments íì¼ì´ ì ì¥ëê¸° ììí©ëë¤. ê²½ê³ : íì¼ì ì¸ ë ì¤í¬ë¦½í¸ê° ììë  ì ìì¼ë¯ë¡ ì¤í¬ë¦½í¸ë¥¼ ì¤ë¨íì§ ë§ì­ìì¤. í´ì íë ¤ë©´ 0ì¼ë¡ ì¤ì  ë°ì´í° ë©í°íë¡ì¸ì±ì ì°ì§ ììµëë¤. ëë¦¬ì§ë§ ììì ë ìëª¨í©ëë¤. ì¶ì¶ì ë³ë ¬ë¡ ì¤ííì§ ë§ì­ìì¤. ì¶ì¶ íë¡ì¸ì¤ì ê° ë¶ë¶ì ëìì ëª¨ë ì¤ííë ê²ì´ ìëë¼ ê°ë³ì ì¼ë¡(íëì©) ì¤íí©ëë¤. VRAMì´ íë¦¬ë¯¸ìì¸ ê²½ì° ì ì©í©ëë¤. ëë²ê¹ì ìí´ ì¶ë ¥ ì¼êµ´ì í¹ì§ì ì ê·¸ë¦½ëë¤. ì¤ìê° ë³íì íì±íí©ëë¤. ê¶ì¥íì§ ììµëë¤. ë¹ì ì ë³í ë¹ëì¤ì ëí ê¹¨ëí alignments íì¼ì ìì±í´ì¼ í©ëë¤. ê·¸ë¬ë ìíë ê²½ì° ì´ ìµìì íì±ííì¬ ì¦ì alignments íì¼ì ìì±í  ì ììµëë¤. ì´ê²ì ìì¢ì ì¶ì¶ ê³¼ì ì ì¬ì©íê³  íì¤ ì´íì ê²°ê³¼ë¡ ì´ì´ì§ ê²ìëë¤. alignments íì¼ì´ ë°ê²¬ëë©´ ì´ ìµìì ë¬´ìë©ëë¤. ëª¨ë  'në²ì§¸' íë ìì ì¶ì¶í©ëë¤. ì´ ìµìì ì¼êµ´ì ì¶ì¶í  ë ê±´ëë¸ íë ìì ì¤ì í©ëë¤. ìë¥¼ ë¤ì´, ê°ì´ 1ì´ë©´ ëª¨ë  íë ììì ì¼êµ´ì´ ì¶ì¶ëê³ , ê°ì´ 10ì´ë©´ ëª¨ë  10ë²ì§¸ íë ììì ì¼êµ´ì´ ì¶ì¶ë©ëë¤. ì¼êµ´ë¤ì ì´ë¯¸ì§ ëë ë¹ëì¤ìì ì¶ì¶í©ëë¤.
ì¶ì¶ íë¬ê·¸ì¸ì 'ì¤ì ' ë©ë´ìì ì¤ì í  ì ììµëë¤ ì¼êµ´ ì²ë¦¬ ì´ í¬ê¸° ë¯¸ë§ì¼ë¡ íì§ë ì¼êµ´ì íí°ë§í©ëë¤. ê¸¸ì´, ê²½ê³ ììì ëê°ì ì ê±¸ì¹ í½ì ë¨ììëë¤. 0ì¼ë¡ ì¤ì íë©´ êº¼ì§ëë¤ ìµìì¸ nfilter/filter íì¼ê³¼ í¨ê» ì¬ì©í©ëë¤. ê¸ì ì ì¸ ì¼êµ´ ì¸ìì ìí ìê³ê°. ê°ì´ ëììë¡ ìê²©í©ëë¤. ìµìì¸ nfilter/filter íì¼ì í¨ê» ì¬ì©í©ëë¤. ê¸ì ì ì¸ ì¼êµ´ ì¸ìì ìí ìê³ê°. ë®ì ê°ì´ ë ìê²©í©ëë¤. ì£¼ì: ì¼êµ´ íí°ë¥¼ ì¬ì©íë©´ ì¶ì¶ ìëê° íì í ê°ìíë¯ë¡ ì íì±ì ë³´ì¥í  ì ììµëë¤. íë ì ì²ë¦¬ ìë¥¼ ë¤ì´ ì ì¡ì ì ì©í  íë ì ë²ì íë ì 10 - 50 ë° 90 - 100ì ê²½ì° --frame-ranges 10-50 90-100ì ì¬ì©í©ëë¤. '-k'(--keep-unchanged)ë¥¼ ì ííì§ ìì¼ë©´ ì íí ë²ìë¥¼ ë²ì´ëë íë ìì´ ì­ì ë©ëë¤. NB: ì´ë¯¸ì§ìì ë³ííë ê²½ì° íì¼ ì´ë¦ì íë ì ë²í¸ë¡ ëëì¼ í©ëë¤! ì¼êµ´ì´ ë°ê²¬ëì§ ìì¼ë©´ ì´ë¯¸ì§ë¥¼ íì íì¬ ì¼êµ´ì ì°¾ìµëë¤. ì¶ì¶ ìëë¥¼ í¬ìíë©´ì ë ë§ì ì¼êµ´ì ì°¾ì ì ììµëë¤. ë¨ì¼ ì«ìë¥¼ ìë ¥íì¬ í´ë¹ í¬ê¸°ì ì¦ë¶ì 360ê¹ì§ ì¬ì©íê±°ë ì«ì ëª©ë¡ì ìë ¥íì¬ íì¸í  ê°ëë¥¼ ì ííê² ì´ê±°í©ëë¤. ë§ì½ alignments íì¼ì ì§ì°ì§ ìì ê²½ì° ìë ¥ íì¼/ë¹ëì¤ìì ì¶ì¶ë ì¼êµ´ì´ í¬í¨ë í´ëë¥¼ ì ìíì¬ ì¼êµ´ì ê±¸ë¬ë¼ ì ììµëë¤. ì´ í´ëê° ì ìë ê²½ì° alignments íì¼ ë´ì ì¡´ì¬íê±°ë ì§ì ë í´ë ë´ì ì¡´ì¬íë ì¼êµ´ë§ ë³íë©ëë¤. ì´ í­ëª©ì ê³µë°±ì¼ë¡ ëë©´ alignments íì¼ ë´ì ìë ëª¨ë  ì¼êµ´ì´ ë³íë©ëë¤. í´ëë ë¹ëì¤ë¥¼ ìë ¥íì¸ì. ë¹ì ì´ ì¬ì©íê³  ì¶ì ì´ë¯¸ì§ íì¼ë¤ì ê°ì§ í´ë ëë ë¹ëì¤ íì¼ì ê²½ë¡ì¬ì¼ í©ëë¤. NB: ì´ í´ëë ìë³¸ ë¹ëì¤ì¬ì¼ í©ëë¤. ëª¨ë¸ í´ë. ë¹ì ì´ ë³íì ì¬ì©íê³ ì íë íë ¨ë ëª¨ë¸ì ê°ì§ í´ëìëë¤. VGGFace2ìì ì¼êµ´ ìë³ ì¸ì½ë©ì ê°ì ¸ì ì ì¥í©ëë¤. ì¶ì¶ ìëë¥¼ ì½ê° ë¦ì¶ì§ë§ 'ì¼êµ´ë³ë¡ ì ë ¬'ì ì¬ì©íë©´ ìê°ì ì ì½í  ì ììµëë¤. ì´ë¯¸ì§ìì ë¹ëì¤ë¡ ë³ííë ê²½ì°ìë§ íìí©ëë¤. ìì¤ íë ìì´ ì¶ì¶ë ìë³¸ ë¹ëì¤(fps ë° ì¤ëì¤ ì¶ì¶ì©)ë¥¼ ìë ¥íì¸ì. (ì íì ) alignments íì¼ì ê²½ë¡. ë¹ìëë©´ alignments íì¼ì´ ê¸°ë³¸ ìì¹ì ì ì¥ë©ëë¤. ì íì ì¼ë¡ ì¶ì¶íì§ ìì ì¬ëì ì´ë¯¸ì§ë¤ì ì ë¬íì¬ ê·¸ ì¬ëë¤ì ì ì¸í©ëë¤. ê°ëì ì¡°ê±´ì´ ë¤ë¥¸ ìì ë¤ìí ì´ë¯¸ì§ì¬ì¼ í©ëë¤. ì¶ì¶ëì§ ìëë° íìí ì´ë¯¸ì§ë¤ ëë ê³µë°±ì¼ë¡ êµ¬ë¶ë ì¬ë¬ ì´ë¯¸ì§ íì¼ì´ ë¤ì´ ìë í´ëë¥¼ ì íí  ì ììµëë¤. ì íì ì¼ë¡ ì²ë¦¬íê³  ì¶ì§ ìì ì¬ëì ì´ë¯¸ì§ë¥¼ ì ë¬íì¬ ê·¸ ì¬ëì ê±¸ë¬ë¼ ì ììµëë¤. ì´ë¯¸ì§ë í ì¬ëì ì ë©´ ëª¨ìµì´ì¬ì¼ í©ëë¤. ì¬ë¬ ì´ë¯¸ì§ë¥¼ ê³µë°±ì¼ë¡ êµ¬ë¶íì¬ ì¶ê°í  ì ììµëë¤. ì£¼ì: ì¼êµ´ íí°ë¥¼ ì¬ì©íë©´ ì¶ì¶ ìëê° íì í ê°ìíë¯ë¡ ì íì±ì ë³´ì¥í  ì ììµëë¤. ì íì ì¼ë¡ ì¶ì¶íê³  ì¶ì ì¬ëì ì´ë¯¸ì§ë¥¼ ì ë¬íì¬ ê·¸ ì¬ëì ì íí©ëë¤. ê°ëì ì¡°ê±´ì´ ë¤ë¥¸ ìì ë¤ìí ì´ë¯¸ì§ì¬ì¼ í©ëë¤. ì¶ì¶í  ë íìí ì´ë¯¸ì§ë¤ ëë ê³µë°±ì¼ë¡ êµ¬ë¶ë ì¬ë¬ ì´ë¯¸ì§ íì¼ì´ ë¤ì´ ìë í´ëë¥¼ ì íí  ì ììµëë¤. ì íì ì¼ë¡ í´ë¹ ì¬ì©ìì ì´ë¯¸ì§ë¥¼ ì ë¬íì¬ ì²ë¦¬í  ì¬ì©ìë¥¼ ì íí©ëë¤. ì´ë¯¸ì§ì í ì¬ëì´ ìë ì ë©´ ì´ìíì¬ì¼ í©ëë¤. ì¬ë¬ ì´ë¯¸ì§ë¥¼ ê³µë°±ì¼ë¡ êµ¬ë¶íì¬ ì¶ê°í  ì ììµëë¤. ì£¼ì: ì¼êµ´ íí°ë¥¼ ì¬ì©íë©´ ì¶ì¶ ìëê° íì í ê°ìíë¯ë¡ ì íì±ì ë³´ì¥í  ì ììµëë¤. ì¶ë ¥ í´ë. ë³íë íì¼ë¤ì´ ì ì¥ë  ê³³ìëë¤. íë¬ê·¸ì¸ë¤ _alignerë¥¼ íµí´ ì²ì ë°ê²¬ë ì ë ¬ë ì¼êµ´ì ì¬ê³µê¸í©ëë¤. íë ììì 45ë ì´ì íì íê±°ë ê·¹ë¨ì ì¸ ê°ëì ìë ì¼êµ´ì ë ì ì ë ¬í  ì ììµëë¤. ì¶ì¶ ìëê° ëë ¤ì§ëë¤. R|ì¬ì©í  ì¶ê° Maskìëë¤. ì¬ê¸°ì ìì±ë ë§ì¤í¬ë ëª¨ë GPU RAMì ì°¨ì§í©ëë¤. ë§ì¤í¬ë¥¼ 0ê°, 1ê° ëë ì¬ë¬ ê° ì íí  ì ìì§ë§ ë ë§ì´ ì íí ìë¡ ì¶ì¶ì ìê°ì´ ë ê±¸ë¦´ ì ììµëë¤. NB: íì¥ ë° êµ¬ì± ìì(í¹ì§ì  ê¸°ë°) ë§ì¤í¬ë ì¶ì¶ ì ìëì¼ë¡ ìì±ë©ëë¤.
L|bisnet-fp: ì ì²´ í¤ë ë§ì¤í¹(ë§ì¤í¬ ì¤ì ìì êµ¬ì± ê°ë¥)ì í¬í¨íì¬ ë§ì¤í¹í  ìì­ì ëí ë³´ë¤ ì êµí ì ì´ë¥¼ ì ê³µíë ë¹êµì  ê°ë²¼ì´ NN ê¸°ë° ë§ì¤í¬ìëë¤.
L|custom: ë§ì¤í¬ ìì­ì ëª¨ë  1 ëë 0ì¼ë¡ ì±ì°ë dummy ë§ì¤í¬ìëë¤(ì¤ì ìì êµ¬ì± ê°ë¥). ìë ëêµ¬ìì ì¬ì©ì ì ì ë§ì¤í¬ë¥¼ ì§ì  ìëì¼ë¡ í¸ì§íë ¤ë ê²½ì°ìë§ íìí©ëë¤. ì´ ë§ì¤í¬ë GPUë¥¼ ì¬ì©íì§ ìì¼ë¯ë¡ ì¶ê° VRAMì ì¬ì©íì§ ììµëë¤.
L|vgg-clear: ëë¶ë¶ì ì ë©´ì ì¥ì ë¬¼ì´ ìë ì¤ë§í¸í ë¶í ì ì ê³µíëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. íë¡í ì¼êµ´ë¤ ë° ì¥ì ë¬¼ë¤ë¡ ì¸í´ ì±ë¥ì´ ì íë  ì ììµëë¤.
L|vgg-obstructed: ëë¶ë¶ì ì ë©´ ì¼êµ´ì ì¤ë§í¸íê² ë¶í í  ì ìëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. ë§ì¤í¬ ëª¨ë¸ì ì¼ë¶ ìë©´ ì¥ì ë¬¼(ìê³¼ ìê²½)ì ì¸ìíëë¡ í¹ë³í íë ¨ëììµëë¤. íë¡í ì¼êµ´ë¤ì íê·  ì´íì ì±ë¥ì ì´ëí  ì ììµëë¤.
L|unet-dfl: ëë¶ë¶ ì ë©´ ì¼êµ´ì ì¤ë§í¸íê² ë¶í íëë¡ ì¤ê³ë ë§ì¤í¬. ë§ì¤í¬ ëª¨ë¸ì ì»¤ë®¤ëí° êµ¬ì±ìë¤ì ìí´ íë ¨ëìì¼ë©° ì¶ê° ì¤ëªì ìí´ íì¤í¸ê° íìíë¤. íë¡í ì¼êµ´ë¤ì íê·  ì´íì ì±ë¥ì ì´ëí  ì ììµëë¤.
ìë ìì± ë§ì¤í¬ë ë¤ìê³¼ ê°ìµëë¤.
L|components: í¹ì§ì  ìì¹ì ìì¹ë¥¼ ê¸°ë°ì¼ë¡ ì¼êµ´ ë¶í ì ì ê³µíëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. í¹ì§ì ì ì¸ë¶ìë ë§ì¤í¬ë¥¼ ë§ë¤ê¸° ìí´ convex hullê° íì±ëì´ ììµëë¤.
L|extended: í¹ì§ì  ìì¹ì ìì¹ë¥¼ ê¸°ë°ì¼ë¡ ì¼êµ´ ë¶í ì ì ê³µíëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. í¹ì§ì ì ì¸ë¶ìë convex hullê° íì±ëì´ ìì¼ë©°, ë§ì¤í¬ë ì´ë§ ìë¡ ë»ì´ ììµã´ë¤.
(ì: '-M unet-dfl vgg-clear', '--masker vgg-obstructed') R|ì¬ì©í  Aligner.
L|cv2-dnn: CPUë§ì ì¬ì©íë í¹ì§ì  ê°ì§ê¸°. ë¹ ë¥´ê³  ììì ë ì¬ì©íì§ë§ ë¶ì íí©ëë¤. GPUë¥¼ ì¬ì©íì§ ìê³  ìê°ì´ ì¤ìí  ëìë§ ì¬ì©íì¸ì.
L|fan: ê°ì¥ ì¢ì aligner. GPUìì  ë¹ ë¥´ê³  CPUìì  ëë¦½ëë¤.
L|external: JSON íì¼ìì 68 í¬ì¸í¸ 2D ëë ë§í¬ ëë ì ë ¬ ë ê²½ê³ ììë¥¼ ê°ì ¸ìµëë¤. (ì ë ¬ ì¤ì ìì êµ¬ì± ê°ë¥) R|ì¬ì©í  ê°ì§ê¸°. ëªëª ê°ì§ê¸°ë¤ì '/config/extract.ini' ëë 'ì¤ì  > ì¶ì¶ íë¬ê·¸ì¸ ì¤ì 'ìì ì¤ì ì´ ê°ë¥í©ëë¤:
L|cv2-dnn: ê°ì¥ ë¯¿ì ì ìê³  ê°ì¥ ììì ë ì¬ì©íë©° CPUë§ì ì¬ì©íë ì¶ì¶ê¸°ìëë¤. ë§ì½ GPUë¥¼ ì¬ì©íì§ ìê³  ìê°ì´ ì¤ìíë¤ë©´ ì¬ì©íì¸ì.
L|mtcnn: ì¢ì ê°ì§ê¸°. CPUììë ë¹ ë¥´ê³  GPUììë ë¹ ë¦ëë¤. ë¤ë¥¸ GPU ê°ì§ê¸°ë¤ë³´ë¤ ë ì ì ììì ì¬ì©íì§ë§ ê°ë ë ë§ì false positivesë¥¼ ëë ¤ì¤ ì ììµëë¤.
L|s3fd: ê°ì¥ ì¢ì ê°ì§ê¸°. CPUìì  ëë¦¬ê³  GPUìì  ë¹ ë¦ëë¤. ë¤ë¥¸ GPU ê°ì§ê¸°ë¤ë³´ë¤ ë ë§ì ì¼êµ´ë¤ì ê°ì§í  ì ìê³  ê³¼ ë ì ì false positivesë¥¼ ëë ¤ì£¼ì§ë§ ììì êµì¥í ë§ì´ ì¬ì©í©ëë¤.
L|external: JSON íì¼ìì ì¼êµ´ ê°ì§ ê²½ê³ ë°ì¤ë¥¼ ê°ì ¸ìµëë¤. (ì¤ì  ê°ì§ìì êµ¬ì± ê°ë¥) R|ë§ì½ ì íëë¤ë©´ input_dirì ë¹ì ì´ ì¶ì¶íê³ ì íë ì¬ë¬ê°ì ë¹ëì¤ ê·¸ë¦¬ê³ /ëë ì´ë¯¸ì§ë¤ì ê°ì§ ë¶ëª¨ í´ëê° ëì¼ í©ëë¤. ì¼êµ´ë¤ì output_dirì ë¶ë¦¬ë íì í´ëì ì ì¥ë©ëë¤. R|ì¬ì©í  ë§ì¤í¬. NB: íìí ë§ì¤í¬ë alignments íì¼ ë´ì ìì´ì¼ í©ëë¤. ë§ì¤í¬ ëêµ¬ë¥¼ ì¬ì©íì¬ ë§ì¤í¬ë¥¼ ì¶ê°í  ì ììµëë¤.
L|none: ë§ì¤í¬ ì°ì§ ë§ì¸ì.
L|bisnet-fp_face: ë§ì¤í¬í  ìì­ì ë³´ë¤ ì êµíê² ì ì´í  ì ìë ë¹êµì  ê°ë²¼ì´ NN ê¸°ë° ë§ì¤í¬ìëë¤(ë§ì¤í¬ ì¤ì ìì êµ¬ì± ê°ë¥). ëª¨ë¸ì´ 'ì¼êµ´' ëë 'ë ê±°ì' ì¤ì¬ì¼ë¡ íë ¨ë ê²½ì° ì´ ë²ì ì bisnet-fpë¥¼ ì¬ì©íì­ìì¤.
L|bisnet-fp_head: ë§ì¤í¬í  ìì­ì ë³´ë¤ ì êµíê² ì ì´í  ì ìë ë¹êµì  ê°ë²¼ì´ NN ê¸°ë° ë§ì¤í¬ìëë¤(ë§ì¤í¬ ì¤ì ìì êµ¬ì± ê°ë¥). ëª¨ë¸ì´ 'í¤ë' ì¤ì¬ì¼ë¡ íë ¨ë ê²½ì° ì´ ë²ì ì bisnet-fpë¥¼ ì¬ì©íì­ìì¤.
L|custom_face: ì¬ì©ì ì§ì  ì¬ì©ìê° ìì±í ì¼êµ´ ì¤ì¬ ë§ì¤í¬ìëë¤.
L|custom_head: ì¬ì©ì ì§ì  ì¬ì©ìê° ìì±í ë¨¸ë¦¬ ì¤ì¬ ë§ì¤í¬ìëë¤.
L|components: í¹ì§ì  ìì¹ì ë°°ì¹ë¥¼ ê¸°ë°ì¼ë¡ ì¼êµ´ ë¶í ì ì ê³µíëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. í¹ì§ì ì ì¸ë¶ìë ë§ì¤í¬ë¥¼ ë§ë¤ê¸° ìí´ convex hullê° íì±ëì´ ììµëë¤.
L|extended: í¹ì§ì  ìì¹ì ë°°ì¹ë¥¼ ê¸°ë°ì¼ë¡ ì¼êµ´ ë¶í ì ì ê³µíëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. ì§íì§ë¬¼ì ì¸ë¶ìë convex hullê° íì±ëì´ ìì¼ë©°, ë§ì¤í¬ë ì´ë§ ìë¡ ë»ì´ ììµëë¤.
L|vgg-clear: ëë¶ë¶ì ì ë©´ì ì¥ì ë¬¼ì´ ìë ì¤ë§í¸í ë¶í ì ì ê³µíëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. ì ì¼êµ´ ë° ì¥ì ë¬¼ë¡ ì¸í´ ì±ë¥ì´ ì íë  ì ììµëë¤.
L|vgg-obstructed: ëë¶ë¶ì ì ë©´ ì¼êµ´ì ì¤ë§í¸íê² ë¶í í  ì ìëë¡ ì¤ê³ë ë§ì¤í¬ìëë¤. ë§ì¤í¬ ëª¨ë¸ì ì¼ë¶ ìë©´ ì¥ì ë¬¼(ìê³¼ ìê²½)ì ì¸ìíëë¡ í¹ë³í íë ¨ëììµëë¤. ì ì¼êµ´ì íê·  ì´íì ì±ë¥ì ì´ëí  ì ììµëë¤.
L|unet-dfl: ëë¶ë¶ ì ë©´ ì¼êµ´ì ì¤ë§í¸íê² ë¶í íëë¡ ì¤ê³ë ë§ì¤í¬. ë§ì¤í¬ ëª¨ë¸ì ì»¤ë®¤ëí° êµ¬ì±ìë¤ì ìí´ íë ¨ëìì¼ë©° ì¶ê° ì¤ëªì ìí´ íì¤í¸ê° íìíë¤. ì ì¼êµ´ì íê·  ì´íì ì±ë¥ì ì´ëí  ì ììµëë¤.
L|predicted: êµì¡ ì¤ì 'Learn Mask(ë§ì¤í¬ íìµ)' ìµìì´ íì±íë ê²½ì°ìë êµì¡ì ë°ì ëª¨ë¸ì´ ë§ë  ë§ì¤í¬ê° ì¬ì©ë©ëë¤. R|ì ê·íë¥¼ ìííë©´ alignerê° ì¶ì¶ ìë ë¹ì©ì¼ë¡ ì´ë ¤ì´ ì¡°ëª ì¡°ê±´ì ì¼êµ´ì ë ì ì ë ¬í  ì ììµëë¤. ë°©ë²ì´ ë¤ë¥´ë©´ ì¸í¸ë§ë¤ ê²°ê³¼ê° ë¤ë¦ëë¤. NB: ì¶ë ¥ ì¼êµ´ìë ìí¥ì ì£¼ì§ ìì¼ë©° alignerì ëí ìë ¥ìë§ ìí¥ì ì¤ëë¤.
L|none: ì¼êµ´ì ì ê·íë¥¼ ìííì§ ë§ì­ìì¤.
L|clahe: ì¼êµ´ì Contrast Limited Adaptive Histogram Equalizationë¥¼ ìíí©ëë¤.
L|hist: RGB ì±ëì íì¤í ê·¸ë¨ì ëì¼íê² í©ëë¤.
L|mean: ì¼êµ´ ììì íê· ì¼ë¡ ì ê·íí©ëë¤. R|ì¤ìë ì¼êµ´ì ìì ì¡°ì ì ìíí©ëë¤. ì´ë¬í ìµì ì¤ ì¼ë¶ìë '/config/convert.ini' ëë 'ì¤ì  > ë³í íë¬ê·¸ì¸ êµ¬ì±'ìì êµ¬ì± ê°ë¥í ì¤ì ì´ ììµëë¤.
L|avg-color: ì¤ìë ì¬êµ¬ì±ìì ê° ìì ì±ëì íê· ì´ ìë³¸ ìììì ë§ì¤í¹ë ìì­ì íê· ê³¼ ëì¼íëë¡ ì¡°ì í©ëë¤.
L|color-transfer: L*a*b* ì ê³µê°ì íê·  ë° íì¤ í¸ì°¨ë¥¼ ì¬ì©íì¬ ìì¤ìì ëì ì´ë¯¸ì§ë¡ ì ë¶í¬ë¥¼ ì ì¡í©ëë¤.
L|manual-balance: ë¤ìí ì ê³µê°ìì ì´ë¯¸ì§ì ë°¸ë°ì¤ë¥¼ ìëì¼ë¡ ì¡°ì í©ëë¤. ì¬ë°ë¥¸ ê°ì ì¤ì íë ¤ë©´ ë¯¸ë¦¬ ë³´ê¸° ëêµ¬ì í¨ê» ì¬ì©íë ê²ì´ ì¢ìµëë¤.
L|match-hist: ì¤ìë ì¬êµ¬ì±ìì ê° ìì ì±ëì íì¤í ê·¸ë¨ì ì¡°ì íì¬ ìë ìììì ë§ì¤í¹ë ìì­ì íì¤í ê·¸ë¨ê³¼ ëì¼íê² ë§ë­ëë¤.
L|seamless-clone: cv2ì ìíí ë³µì  ê¸°ë¥ì ì¬ì©íì¬ ììì ííííì¬ ë§ì¤í¬ ì¬ìì ê·¹ë¨ì ì¸ gradientsì ì ê±°í©ëë¤. ì¼ë°ì ì¼ë¡ ë§¤ì° ë§ì¡±ì¤ë¬ì´ ê²°ê³¼ë¥¼ ì ê³µíì§ ììµëë¤.
L|none: ìì ì¡°ì ì ìííì§ ììµëë¤. R|ë³íë ì´ë¯¸ì§ë¥¼ ì¶ë ¥íë ë° ì¬ì©í  íë¬ê·¸ì¸ìëë¤. ê¸°ë¡ ì¥ì¹ë '/config/convert.ini' ëë 'ì¤ì  > ë³í íë¬ê·¸ì¸ êµ¬ì±:'ìì êµ¬ì±í  ì ììµëë¤.
L|ffmpeg: [video] ë³íë ê²°ê³¼ë¥¼ ë°ë¡ videoë¡ ìëë¤. ìë ¥ì´ ìì ìë¦¬ì¦ì¸ ê²½ì° '-ref'(--reference-video) íë¼ë¯¸í°ë¥¼ ì¤ì í´ì¼ í©ëë¤.
L|gif : [ì ëë©ì´ì ì´ë¯¸ì§] ì ëë©ì´ì gifë¥¼ ë§ë­ëë¤.
L|opencv: [ì´ë¯¸ì§] ê°ì¥ ë¹ ë¥¸ ì´ë¯¸ì§ ìì±ê¸°ì´ì§ë§ ë¤ë¥¸ íë¬ê·¸ì¸ì ë¹í´ ìµìê³¼ íìì´ ì ìµëë¤.
L|patch: [ì´ë¯¸ì§] ìë íë ìì ì¼êµ´ì ë¤ì ì½ìíë ë° íìí ë³í íë ¬ê³¼ í¨ê» ìì êµì²´ë ì¼êµ´ í¨ì¹ë¥¼ ì¶ë ¥í©ëë¤.
L|pillow: [images] opencvë³´ë¤ ëë¦¬ì§ë§ ë ë§ì ìµìì´ ìê³  ë ë§ì íìì ì§ìí©ëë¤. ìµì¢ ì¶ë ¥ íë ìì í¬ê¸°ë¥¼ ì´ ìë§í¼ ì¡°ì í©ëë¤. 100%%ë ìë³¸ì ì°¨ììì íë ìì ì¶ë ¥í©ëë¤. 50%%ë ì ë° í¬ê¸°ìì, 200%%ë ë ë°° í¬ê¸°ìì ì´ ë°±ë¶ì¨ë¡ êµì²´ë ë©´ì í¬ê¸°ë¥¼ ì¡°ì í©ëë¤. ìì ê°ì ì¼êµ´ì íëíê³ , ìì ê°ì ì¼êµ´ì ì¶ìí©ëë¤. ì´ë¯¸ ì¼êµ´ì íì§íì¬ alignments íì¼ì ì¡´ì¬íë íë ìë¤ì ì¤íµí©ëë¤ íì§ë ì¼êµ´ì ëì¤í¬ì ì ì¥íì§ ììµëë¤. ê·¸ì  alignments íì¼ì ë§ë­ëë¤ ì´ë¯¸ ì¶ì¶ëìê±°ë alignments íì¼ì ì¡´ì¬íë íë ìë¤ì ì¤íµí©ëë¤ ëª¨ë¸ì ë°ê¿ëë¤. A -> Bìì ë³ííë ëì  B -> Aë¡ ë³í ìë³¸ ë¹ëì¤/ì´ë¯¸ì§ì ìë ì¼êµ´ì ìµì¢ ì¼êµ´ì¼ë¡ ë°ê¿ëë¤.
ë³í íë¬ê·¸ì¸ì 'ì¤ì ' ë©ë´ìì êµ¬ì±í  ì ììµëë¤ ë³íì ìííê¸° ìí ìµë ë³ë ¬ íë¡ì¸ì¤ ììëë¤. ì´ë¯¸ì§ ë³íì ìì¤í RAMì ë¶ë´ì´ í¬ê¸° ëë¬¸ì íë¡ì¸ì¤ê° ë§ê³  ëª¨ë  íë¡ì¸ì¤ë¥¼ ìì©í  RAMì´ ì¶©ë¶íì§ ìì ê²½ì° ë©ëª¨ë¦¬ê° ë¶ì¡±í  ì ììµëë¤. ì´ê²ì 0ì¼ë¡ ì¤ì íë©´ ì¬ì© ê°ë¥í ìµëê°ì ì¬ì©í©ëë¤. ì¼ë§ë¥¼ ì¤ì íë  ìì¤íìì ì¬ì© ê°ë¥í ê²ë³´ë¤ ë ë§ì íë¡ì¸ì¤ë¥¼ ì¬ì©íë ¤ê³  ìëíì§ ììµëë¤. ë¨ì¼ íë¡ì¸ì¤ê° íì±íë ê²½ì° ì´ ì¤ì ì ë¬´ìë©ëë¤. ê²ì¶ë ì¼êµ´ì alignerì ë¤ì ê³µê¸íë íììëë¤. ì¼êµ´ì´ alignerì ë¤ì ê³µê¸ë  ëë§ë¤ ê²½ê³ ììê° ìë ì¡°ì ë©ëë¤. ê·¸ë° ë¤ì ê° ë°ë³µìì ìµì¢ í¹ì§ì ì íê· ì êµ¬íë¤. 'micro-jitter'ë¥¼ ì ê±°íë ë° ëìì´ ëì§ë§ ì¶ì¶ ìëê° ëë ¤ì§ëë¤. ì¼êµ´ì´ alignerì ë¤ì ê³µê¸ëë íìê° ë§ììë¡ micro-jitter ì ê² ë°ìíì§ë§ ì¶ì¶ì ë ì¤ë ìê°ì´ ê±¸ë¦½ëë¤. ì¶ì¶ë ì¼êµ´ì ì¶ë ¥ í¬ê¸°ìëë¤. íë ¨íë ¤ë ëª¨ë¸ì´ íìí í¬ê¸°ë¥¼ ì§ìíëì§ ê¼­ íì¸íì¸ì. ì´ê²ì ê³ í´ìë ëª¨ë¸ì ëí´ìë§ ë³ê²½íë©´ ë©ëë¤. ì¬ì©ì --frame-ranges ì¸ìë¥¼ ì¬ì©íë©´ ë³ê²½ëì§ ìì íë ìì ë²ë¦¬ì§ ìì ê²°ê³¼ê° ì¶ë ¥ë©ëë¤. ì¶ë ¥ ì¤ì  