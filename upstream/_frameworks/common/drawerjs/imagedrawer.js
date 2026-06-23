var ImageDrawer = (function () {

	var $this = {};
    var images = {};
    var activeItem = { element: null, index: null };
    var noImageValue = '{\n  "objects": [],\n  "background": ""\n}';
    var windowElement = '#pp_image_editor';
    var buttonClose = 'button.btn_close';
    var buttonPublish = 'button.btn_publish';
    var isInitialized = false;
    var elementWithDrawer = '.pp_image_editor .scrollbarY .viewport';
    var borderOffset = 35;
    var isEditorVisible = false;

    function initImageEditorWindow()
    {
        $(buttonClose, windowElement).click(function(){
                if(drawer.api.getCanvasAsJSON() !== noImageValue){
                    confirmCustom(l('delete_image'), function(){
                        setTimeout(function(){
                            $this.close();
                        }, 250)
                    })
                }else{
                    $this.close();
                }
            });
        $(buttonPublish, windowElement).click(function(){
            $this.save();
        });
    }

    function initImageEditor()
    {
            var drawerPlugins = [
                // Drawing tools
                'Pencil',
                'Eraser',
                //'Text',
                'Line',
                'ArrowOneSide',
                'ArrowTwoSide',
                'Triangle',
                'Rectangle',
                'Circle',
                //'Image',
                //'BackgroundImage',
                //'Polygon',
                //'ImageCrop',

                // Drawing options
                //'ColorHtml5',
                'Color',
                'ShapeBorder',
                'BrushSize',
                'OpacityOption',

                'LineWidth',
                'StrokeWidth',

                //'Resize',
                'ShapeContextMenu',
                //'CloseButton',
                'OvercanvasPopup',
                'OpenPopupButton',
                //'MinimizeButton',
                //'ToggleVisibilityButton',
                //'MovableFloatingMode',
                //'FullscreenModeButton',

                'TextLineHeight',
                'TextAlign',

                'TextFontFamily',
                'TextFontSize',
                'TextFontWeight',
                'TextFontStyle',
                'TextDecoration',
                'TextColor',
                'TextBackgroundColor'
            ];

            // drawer is created as global property solely for debug purposes.
            // doing  in production is considered as bad practice

            var drawerWidth = $('.pp_image_editor .scrollbarY .viewport').width();// - drawerBorderOffset;
            var drawerHeight = $('.pp_image_editor .scrollbarY .viewport').height() - borderOffset * 2;

            console.log('drawerWidth and drawerHeight', drawerWidth, drawerHeight);

            var drawerLocalization =  {
                'Free drawing mode': l('drawer_free_drawing_mode'),
                'Eraser': l('drawer_eraser'),

                // shape context menu plugin
                'Bring forward': l('drawer_bring_forward'),
                'Send backwards': l('drawer_send_backwards'),
                'Bring to front': l('drawer_bring_to_front'),
                'Send to back': l('drawer_send_to_back'),
                'Duplicate': l('drawer_duplicate'),
                'Remove': l('delete'),

                // brush size plugin
                'Size:': l('drawer_size'),

                // colorpicker plugin
                'Fill:': l('drawer_fill'),
                'Transparent': l('drawer_transparent'),

                // shape border plugin
                'Border:': l('drawer_border'),
                'None': l('drawer_none'),

                // arrow plugin
                'Draw an arrow': l('drawer_draw_an_arrow'),
                'Draw a two-sided arrow': l('drawer_draw_a_two-sided_arrow'),
                'Lines and arrows': l('drawer_lines_and_arrows'),

                // circle plugin
                'Draw a circle': l('drawer_draw_a_circle'),

                // line plugin
                'Draw a line': l('drawer_draw_a_line'),

                // rectangle plugin
                'Draw a rectangle': l('drawer_draw_a_rectangle'),

                // triangle plugin
                'Draw a triangle': l('drawer_draw_a_triangle'),

                // base shape
                'Click to start drawing a ': l('drawer_click_to_start_drawing_a'),
                'Opacity:': l('drawer_opacity'),
                'Border type:': l('drawer_border_type'),

                'Line width:': l('drawer_line_width'),
                'Stroke width:': l('drawer_stroke_width'),
            };

            window.drawer = new DrawerJs.Drawer(null, {
                plugins: drawerPlugins,
                corePlugins: [
                    'Zoom' // use null here if you want to disable Zoom completely
                ],
                pluginsConfig: {
                    Image: {
                        scaleDownLargeImage: true,
                        maxImageSizeKb: 10240, //1MB
                        cropIsActive: true
                    },
                    BackgroundImage: {
                        scaleDownLargeImage: true,
                        maxImageSizeKb: 10240, //1MB
                        //fixedBackgroundUrl: '/examples/redactor/images/vanGogh.jpg',
                        imagePosition: 'center',  // one of  'center', 'stretch', 'top-left', 'top-right', 'bottom-left', 'bottom-right'
                        acceptedMIMETypes: ['image/jpeg', 'image/png', 'image/gif'] ,
                        dynamicRepositionImage: true,
                        dynamicRepositionImageThrottle: 100,
                        cropIsActive: false
                    },
                    Text: {
                        editIconMode : false,
                        editIconSize : 'large',
                        defaultValues : {
                            fontSize: 72,
                            lineHeight: 2,
                            textFontWeight: 'bold'
                        },
                        predefined: {
                            fontSize: [8, 12, 14, 16, 32, 40, 72],
                            lineHeight: [1, 2, 3, 4, 6]
                        }
                    },
                    Zoom: {
                        enabled: false,
                        showZoomTooltip: true,
                        useWheelEvents: true,
                        zoomStep: 1.05,
                        defaultZoom: 1,
                        maxZoom: 32,
                        minZoom: 1,
                        smoothnessOfWheel: 0,
                        //Moving:
                        enableMove: true,
                        enableWhenNoActiveTool: true,
                        enableButton: true
                    }
                },
                toolbars: {
                    drawingTools: {
                        position: 'top',
                        positionType: 'outside',
                        customAnchorSelector: '#custom-toolbar-here',
                        compactType: 'scrollable',
                        hidden: false,
                        toggleVisibilityButton: false,
                        fullscreenMode: {
                            position: 'top',
                            hidden: false,
                            toggleVisibilityButton: false
                        }
                    },
                    toolOptions: {
                        position: 'bottom',
                        positionType: 'outside',
                        compactType: 'scrollable',
                        hidden: false,
                        toggleVisibilityButton: false,
                        fullscreenMode: {
                            position: 'bottom',
                            compactType: 'popup',
                            hidden: false,
                            toggleVisibilityButton: false
                        }
                    },
                    settings : {
                        position : 'right',
                        positionType: 'outside',
                        compactType : 'scrollable',
                        hidden: true,
                        toggleVisibilityButton: false,
                        fullscreenMode: {
                            position : 'right',
                            hidden: false,
                            toggleVisibilityButton: false
                        }
                    }
                },
                defaultActivePlugin : { name : 'Pencil', mode : 'lastUsed'},
                debug: true,
                activeColor: '#000000',
                transparentBackground: true,
                align: 'floating',  //one of 'left', 'right', 'center', 'inline', 'floating'
                lineAngleTooltip: { enabled: true, color: 'blue',  fontSize: 15},

                showInElement: '#pp_image_editor .overview',
                tooltipInElement: '#pp_image_editor',
                borderCss: 'none',
                borderCssEditMode: 'none',
                defaultImageUrl: null,
                exitOnOutsideClick: false,

                texts: drawerLocalization
            }, drawerWidth, drawerHeight);

            $('#pp_image_editor .overview').append(window.drawer.getHtml());
            window.drawer.onInsert();
            isInitialized = true

            $(window).on('resize', function() {
                $this.resize();
            });
    }

    function setImageEditorWindow(show)
    {
        show = show || 'show';

        $(windowElement).one('hide.bs.modal',function(){

        }).one('hidden.bs.modal',function(){
            isEditorVisible = false;
            checkOpenModal();
            elementWithDrawerHide();
        }).one('shown.bs.modal',function(){
            if(isInitialized === false) {
                initImageEditor();
            }
            drawer.api.startEditing();
            elementWithDrawerShow();
            isEditorVisible = true;
            $this.resize();
        }).one('show.bs.modal',function(){
            if(isInitialized) {
                drawer.api.stopEditing();
            }
        }).modal(show);
    }

    $this.show = function(element, index) {

        var index = index || null;
        if(index === null) {
            index = $(element).attr('id');
        }

        activeItem.element = element;
        activeItem.index = index;

        var imageSrc = $this.getImageSrc(index);
        if(typeof drawer !== 'undefined') {
            drawer.api.loadCanvasFromData(imageSrc);
        }

        setImageEditorWindow('show');
    }

    $this.save = function() {
        var imageIndex = getActiveItemIndex();
        var imageSrc = drawer.api.getCanvasAsJSON();
        var imageElement = getActiveItemElement();
        if(imageSrc !== noImageValue) {
            images[imageIndex] = {
                src: drawer.api.getCanvasAsJSON(),
                image: drawer.api.getCanvasAsImage(),
                element: getActiveItemElement()
            }
            $(getActiveItemElement()).addClass('saved');
        } else {
            deleteImage(imageIndex);
        }

        if(imageElement) {
            checkTextareaCommentUploadImage($(imageElement));
        }

        setImageEditorWindow('hide');
    }

    $this.close = function(index) {
        var index = index || getActiveItemIndex();
        var imageElement = getImageElementByIndex(index);
        if(imageElement) {
            deleteImage(index);
            $(imageElement).removeClass('saved');
            checkTextareaCommentUploadImage($(imageElement));
        }

        setImageEditorWindow('hide');

        if(typeof drawer !== 'undefined') {
            drawer.api.loadCanvasFromData(noImageValue);
        }
    }

    $this.closeIm = function()
    {
        $this.close('im');
    }

    $this.closeWallPost = function()
    {
        $this.close('wall_post');
    }

    $this.getImage = function(index) {
        var image = '';
        if(index in images) {
            image = images[index].image;
        }
        return image;
    }

    $this.getImageSrc = function(index) {
        console.log('noImageValue', noImageValue);
        var imageSrc = noImageValue;
        if(index in images) {
            imageSrc = images[index].src;
        }
        return imageSrc;
    }

    $this.deactivateEditor = function(index) {
        if(index in images) {
            $(images[index].element).removeClass('saved');
            drawer.api.loadCanvasFromData(noImageValue);
        }
    }

    $this.resize = function() {
        if(isEditorVisible) {
            var drawerWidth = $('.pp_image_editor .scrollbarY .viewport').width();
            var drawerHeight = $('.pp_image_editor .scrollbarY .viewport').height() - borderOffset * 2;
            drawer.api.setSize(drawerWidth, drawerHeight);
            drawer.trigger(drawer.EVENT_CANVAS_RESIZING);
        }
    }

    function deleteImage(index)
    {
        if(index in images) {
            delete images[index];
        }
    }

    function getImageElementByIndex(index)
    {
        var imageElement = null;
        if(index in images) {
            imageElement = images[index].element;
        }
        return imageElement;
    }

    function getActiveItemIndex()
    {
        return activeItem.index;
    }

    function getActiveItemElement()
    {
        return activeItem.element;
    }

    function elementWithDrawerHide()
    {
        $(elementWithDrawer).css('opacity', 0);
    }

    function elementWithDrawerShow()
    {
        $(elementWithDrawer).fadeTo(200, 1);
    }

    $(function(){
        initImageEditorWindow();
    });

	return $this;
}());