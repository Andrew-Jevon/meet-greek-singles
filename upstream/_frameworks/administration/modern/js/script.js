var _dzThumbnailWidth = 195,
	_dzThumbnailHeight = 195;

$(function(){

	$win.on('resize',function(){
        $('.tooltip_error').tooltip('hide');
    })


	$doc.keydown(function(e) {
        var key=e.which?e.which:e.keyCode, $target=$(e.target);

        if(key === 13 && !$target.is('.lang_search') && !$target.closest('.language_words')[0] && !$target.is('textarea')){
            $('.btn_submit').first().click();
            return false;
        }
        if (key === 83 && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            $('.btn_submit').first().click();
            return false;
        }
        return true;
    });

	$('.js_back').click(function() {
		history.back();
		return false;
	});


    $jq('body').on('click', '.modal', function(e){
        closeAlert(e);
    }).on('input', 'input:text', function(){
		hideError(this)
	}).on('focus', 'input:text', function(){
	})

	$('.icon_rotate').click(function(){
       rotatePhoto(this);
       return false;
    });

	$('.btn_submit').click(function() {
		$('.error').tooltip('hide');
        var $formSubmit=$(this).parents('form'),
            $urlVideoMainPage=$('#input_main_page_urban_video_code, #input_main_page_video_code');
        if($urlVideoMainPage[0]
           &&$('#map_on_main_page_urban, #main_page_background_type').val()=='video'){
            var yCode=$.trim($urlVideoMainPage.val());
            if(!yCode){
                showErrorToScroll($urlVideoMainPage,l('please_enter_youtube_video_id'));
                return false;
            }
            yCode=(yCode.match(/(?:^|\/|v=)([\w\-]{11,11})(?:\?|&|#|$)/) || [])[1];
            if (!yCode) {
                showErrorToScroll($urlVideoMainPage,l('youtube_video_id_not_correct'));
                return false;
            } else {
                $formSubmit.submit();
            }
        } else {
            $formSubmit.submit();
        }
        return false;
    });

	$('div.alert:not(.alert-info-1):not(.alert-no-header):visible').delay(2000).animate({opacity:.3,marginTop:0,marginBottom:0,paddingBottom:0,paddingTop:0,height:'toggle'}, 300);
	$('div.alert.alert-no-header:visible').delay(2000).animate({opacity:.3,marginTop:0,marginBottom:'-3.5rem',paddingBottom:0,paddingTop:0,height:'toggle'}, 300);

	$('input.i_radio, input.i_checkbox').on('ifChanged', function (e) {
		$(this).trigger('change', e);
	}).on('ifClicked', function (e) {
		$(this).trigger('click', e);
	});

	$('.select2').select2({dropdownAutoWidth:true});

	$('.select_change_language').change(function(){
		redirectUrl(this.value);
	})

	$('.menu_hor_bl .navbar-nav .nav-item.active > a').click(function(){
		return false;
	});

	$('.menu-main-collapse').click(function(){
		$.cookie('admin_menu_main_collapse', $(this).is('.is-active')?1:0, {path:'/'});
	})

	$('ul.lmenu_page li.active a, ul.lmenu_page li a.active').click(function(){
		return false;
	})
})

function resizeHrMenu(){
	prepareHrMenu();
	$win.on('resize', prepareHrMenu);
}

function prepareHrMenu(){
	var $menu=$jq('#main-menu-navigation-hr');
	if ($menu.is('.to_expanded')) {
		$menu.removeClass('to_expanded');
	}
	if ($menu[0].offsetHeight > 145) {
		$menu.addClass('to_expanded');
	} else {
		$menu.removeClass('to_expanded');
	}
}

function closeAlert(e){
	if(e){
        var $targ=$(e.target);

        if ($targ.is('.custom_confirm_modal')||$targ.closest('.custom_confirm_modal')[0]){
            return false;
        }
    }

    if ((e&&($targ.is('.modal')||$targ.is('.modal-dialog')))||!e){
        $('.custom_modal_alert.show').modal('hide');
        $('.custom_modal.show').modal('hide');
        return false;
    }
}

function alertCustom(msg, title, hClose, btnOk, classModal)
{
    var fnBackdrop = false;
    if($('.pp_stream_title.in')[0]){
        //fnBackdrop = true;
    }
    var fn=function(){
        if(typeof(hClose)!='function')hClose=closeAlert;
        title=defaultFunctionParamValue(title, l('alert_html_alert'));//l('alert_html_alert') l('alert_success')
        btnOk=btnOk||l('alert_html_ok');
        var backdrop='true';
        if($('.modal-backdrop.in')[0] && !fnBackdrop){
            backdrop='false';
        }
        classModal=classModal||'';
        var $pp=$('<div class="modal fade bs-example-modal-sm custom_modal custom_modal_alert '+classModal+'" tabindex="-1" role="dialog" data-backdrop="'+backdrop+'">'+
                '<div class="modal-dialog modal-sm" role="document">'+
                    '<div class="modal-content">'+
                        '<div class="modal-header">'+
                            '<h3 class="modal-title">'+title+'</h3>'+
                        '</div>'+
                        '<div class="modal-body">'+msg+'</div>'+
                        '<div class="modal-footer">'+
                            '<button type="button" class="btn btn-success">'+
                            '<span class="icon check"></span>'+btnOk+'</button>'+
                        '</div>'+
                    '</div>'+
                '</div>'+
              '</div>')
        .appendTo('body')
        .on('hidden.bs.modal', function(){
            $pp.remove();
        })
        .modal('show');
        $('.btn-success', $pp).click(function(){hClose()});
    }

    if($('.custom_modal_alert')[0]){
        $('.custom_modal_alert').eq(0).one('hidden.bs.modal', fn);
        closeAlert();
    }else{
        closeAlert();
        fn();
    }
}

function confirmCustom(msg, handler, hCancel_or_title, title, btnOk, btnCancel, hideCancel, noCloseOk) {
    var fn=function(){
        btnOk=btnOk||l('alert_html_ok');
        btnCancel=btnCancel||l('cancel');
        var titleDefault=title,
        noCancel=(typeof(hCancel_or_title) != 'function');
		title=(noCancel ? hCancel_or_title : title)||l('are_you_sure');
        var cancelHtml='<button type="button" class="btn btn-secondary">'+
                   '<span><span class="icon remove"></span>'+btnCancel+'</span></button>',
            titleHtml='<div class="modal-header">'+
                    '<h3 class="modal-title">'+title+'</h3>'+
                  '</div>';

        if(hideCancel)cancelHtml='';

        if(titleDefault=='')titleHtml='';
        var backdrop='static';
        //if($('.modal-backdrop.in')[0]){
            //backdrop='false';
        //}

        var $pp=$('<div class="modal fade bs-example-modal-sm custom_modal custom_confirm_modal custom_modal_alert" tabindex="-1" role="dialog" data-backdrop="'+backdrop+'">'+
                '<div class="modal-dialog modal-sm modal-dialog-centered" role="document">'+
                    '<div class="modal-content">'+
                        titleHtml+
                        '<div class="modal-body"><p>'+msg+'</p></div>'+
                        '<div class="modal-footer">'+
                            '<div class="double">'+
                                cancelHtml+
                                '<button type="button" class="btn btn-success  ml-1">'+
                                '<span><span class="icon check"></span>'+btnOk+'</span></button>'+
                            '</div>'+
                        '</div>'+
                    '</div>'+
                '</div>'+
              '</div>')
        .appendTo('body')
        .on('hidden.bs.modal', function () {
            $pp.remove();
        }).modal('show');

        var button='.btn-secondary';
        if(!noCloseOk)button +=',.btn-success';
        $(button, $pp).on('click',function(){closeAlert()});

        $('.btn-success', $pp).click(function(){
            handler($(this));
            if(noCloseOk)$('button', $pp).prop('disabled', true)
        });
        if (!noCancel) $('.btn-secondary', $pp).click(hCancel_or_title);
    }

    if($('.custom_modal_alert')[0]){
        $('.custom_modal_alert').eq(0).one('hidden.bs.modal', fn);
        closeAlert();
    }else{
        closeAlert();
        fn();
    }
}

function showErrorFocus($sel, msg, hide, nofocus){
    if(!$sel.is(':focus'))return;
    showError($sel, msg, hide, nofocus)
}

function showError($sel, msg, hide, nofocus){
    hide=hide||false;
    nofocus=nofocus||false;

    if(!hide&&!nofocus)$sel.focusEl();
    $sel.attr('data-original-title', msg)
        .prop('disabled', false).tooltip({
        template:'<div class="tooltip tooltip_error" role="tooltip">'+
                    '<div class="arrow"></div>'+
                    '<div class="tooltip-inner"></div>'+
                 '</div>',
        trigger:'manual',
        title: msg,
        animation:true
    }).on('hidden.bs.tooltip', function(){
        $sel.removeClass('show_error');
        //console.log('hidden');
        //.tooltip('destroy')
    }).addClass('wrong');

    if (hide) {
        $sel.tooltip('hide');
    }else{
        if($sel.is('.show_error')&&$sel.attr('aria-describedby')){
            var tId=$sel.attr('aria-describedby'),
                msgOld=$('#'+tId).find('.tooltip-inner').text();
            if (msgOld==msg) {
                $('#'+tId).find('.tooltip-inner').text(msg);
            }else{
                $sel.tooltip('show').addClass('show_error');
            }
        } else {
            $sel.tooltip('show').addClass('show_error');
        }
    }

    if ($sel.closest('.bootstrap-select')[0]) {
        $sel.closest('.bootstrap-select').addClass('wrong');
    } else if ($sel[0].id=='blog_subject') {
        $sel.closest('.title').addClass('wrong');
    }
}

function showErrorToScroll($el,msg){
    var i=1;
    $('body, html').animate({scrollTop:0},1,function(){
        if(i){
            showError($el, msg);
            i=0;
        }
    })
}

function focusError($sel){
    if($sel.is('.show_error')&&$sel.attr('aria-describedby'))return;
    if($sel.is('.wrong'))$sel.tooltip('show')
}

function blurError($sel){
    if($sel.is('.wrong'))$sel.tooltip('hide').removeClass('show_error');
}

function hideError(sel){
    var $sel=$(sel);
	if (!$sel[0]) {
		return;
	}
    $sel.removeClass('wrong').tooltip('hide').removeClass('show_error');
    if ($sel.closest('.bootstrap-select')[0]) {
        $sel.closest('.bootstrap-select').removeClass('wrong');
    } else if ($sel[0].id=='blog_subject') {
        $sel.closest('.title').removeClass('wrong');
    }
}

function removeErrorAll(){
	$('.show_error').each(function(){
		hideError(this)
	})
}

function prepareLangAdmin(){
    var $linkLang=$('#header_language .language');
    if ($linkLang[0]) {
        $('#pp_language').autocolumnlist({columns: 4, clickEmpty:function(){
        }});
    }
}

function validateTwoFieldsCustom(field,name,field2,name2) {
	if (field.value != field2.value){
		var msg = MSG_TWO_FIELDS.replace('%1', name);
		msg = msg.replace('%2', name2);
		alertCustom(msg);
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

function adminReloadPage(){
    var urlParts = window.location.href.split('#');
    window.location.href = urlParts[0];
}

function logLoadPageTime(){
    $(window).on('load', function(){
        var endTime = new Date(), elapsedTime = Number(endTime-_appStartTime);
        console.log("TIME LOAD PAGE: " + Number(elapsedTime/1000) + " s (" + elapsedTime + " ms)");
    })
}

function setColorClass(tr)
{
    tr.attr('class', 'color_set');
    tr.children('#decor_l').attr('class', 'decor_set_l');
    tr.children('#decor_r').attr('class', 'decor_set_r');
}

function setSelColorClass(setClass, tr)
{
    if (setClass) {
        tr.attr('class', 'color');
        tr.children('#decor_l').attr('class', 'decor_l');
        tr.children('#decor_r').attr('class', 'decor_r');
    }
}

function fixHelperModified(e, tr) {
    var $originals = tr.children();
	tr.children().each(function(index){
		$(this).width($originals.eq(index).width());
		$(this).parent().css({'border-collapse' : 'collapse'});
	});
	return tr;
};

function locationReplaceForm(form, url) {
	url += '?';
	var tot = form.elements.length;
	for (var i = 0; i < tot; i++) {
		var e = form.elements[i];
		if (! isEmpty(e)) {
			url += e.name + '=' + e.value;
			if (i < tot -1) {
				url+='&';
			}
		}
	}
	location.replace(url);
}

function setDataSizeGallery($el, src) {
	var img = new Image();
	img.onload = function() {
		var w=this.width, h=this.height;
		if (w && h) {
			var wW=$win.width()-80;
			if (w > wW) {
				var d=wW/w;
				w=wW;
				h = Math.round(h * d, 1);
			}
			$el.attr('data-size', w+'x'+h);
		}
	}
	img.src = src;
}

function rotatePhoto(e){

    var id=$(e).attr('data-photo-id');
    var user_id=$(e).attr('data-user-id');
    var size=$(e).attr('data-photo-size');

    $(e).hide();

    $.post('ajax.php',{cmd:'rotate_photo',photo_id:id,angle:90,user_id:user_id},function(res){
        if(res==1){
            $('#photo_'+id).attr('src', urlAddUniqueVersionParam($('#photo_'+id).attr('src')));
        }
        $(e).show();
    });
}

function addChildrenLoader($btn){
    var $iconFa = $btn.find('.icon_fa, .icon');
    if($iconFa[0]){
        $iconFa.addChildrenLoader();
    }else{
        $btn.addChildrenLoader();
    }
}

function removeChildrenLoader($btn){
    var $iconFa = $btn.find('.icon_fa, .icon');
    if($iconFa[0]){
        $iconFa.removeChildrenLoader();
    }else{
        $btn.removeChildrenLoader();
    }
}

function _initLightbox(){
    $(function(){
		$('.lightbox, .lightbox_pics_im, .timeline_photo, .timeline_photo_comment, .edit_image_gallery').each(function(){
			var $el=$(this),$img=$el.find('img'), sel='',src='';
			if (this.id) {
				sel='#'+this.id;
			} else {
				var id=$img[0].id + '_lb';
				$el.attr('id', id);
				sel='#'+id;
			}
			$el.closest('div').find('.mod_im_msg_image_desc').addClass('no_gallery');
			if ($el.is('.edit_image_gallery')) {
				src=$el.attr('href');
			} else if ($img[0]) {
				src=$img.attr('src');
			}
			if (sel && src) {
				setDataSizeGallery($el, src);
				initPhotoSwipeFromDOM(sel);
			}
		})
	})
}

function partnerCheckboxCheckUncheckAdmin(checkboxArea)
{
	var checkboxArea = checkboxArea || '.checkbox_fields_area input[type="checkbox"]';
	$(document).ready(function() {
		$(checkboxArea).click(function(){
			var currentCheckboxValue = $(this).val()*1;
			var currentCheckboxName = $(this).attr('name');
			$('input[name="' + currentCheckboxName + '"]').each(function(){
				if(currentCheckboxValue != 0) {
					if($(this).attr('value') == 0) {
						$(this).prop('checked', false).iCheck('update');
					}
				} else {
					if($(this).attr('value') != 0) {
						$(this).prop('checked', false).iCheck('update');
					}
				}
			});
		});
	});
}

function choiceChkbox(ch, chkbox) {
    if(ch.is(':checked')) {
        chkbox.prop("checked", true).iCheck('update');
    }else{
        chkbox.prop("checked", false).iCheck('update');
    }
}

// geo editor
function geoUpdateItem(id_item) {
    var el = $('#'+id_item),
        val = el.val();
    if (val != el.data('current')) {
        $('#preloader_'+id_item).show();
        $.post(window.location.href, {cmd: 'edit', id: id_item, name: val}, function(data){
            $('#preloader_'+id_item).hide();
            if (data == 'ok') {
                el.data('current', val);
            }
        });
    }
}

function geoDeleteItem(id_item, type)
{
    geoAction('delete', id_item, type);
}

function geoHideItem(id_item, type)
{
    geoAction('hide', id_item, type);
}

function geoShowItem(id_item, type)
{
    geoAction('show', id_item, type);
}

function geoAction(cmd, id_item, type)
{
    if (type == 1) {
        id_item = getChoiceSelectChkbox();
    }

    console.log('start');

    $.post(window.location.href, {cmd: cmd, item: id_item}, function(data) {
        if (data == 'ok') {
            if (type == 1) {
                adminReloadPage();
            } else {
                if ($('[id ^= block_]').length > 1) {
                    if(cmd == 'delete') {
                        $('#block_'+id_item +', #block_action_'+id_item).animate({opacity: 0, height: 0, marginTop: 0, marginBottom:0}, 400,function(){$(this).remove()});
                    } else if (cmd == 'hide') {
                        $('#hide_item_' + id_item).hide();
                        $('#show_item_' + id_item).show();
                    } else if (cmd == 'show') {
                        $('#show_item_' + id_item).hide();
                        $('#hide_item_' + id_item).show();
                    }
                } else {
                    adminReloadPage();
                }
            }
        }
	});
}

function CBoxNoteAdmin(ch, chkbox){
	if(ch.is(':checked')) {
		chkbox.prop("checked", true).iCheck('update');
	}else{
		chkbox.prop("checked", false).iCheck('update');
	}
}

function chartResetTooltipMax() {
	$('.chartist-tooltip-point-active').remove();
}

function chartCreateTooltipMax(){
	$('.point_active').each(function(){
		var $el=$(this),
			$toolTip=$('<div class="chartist-tooltip chartist-tooltip-point-active">'),
			$chart=$('#areaGradient');

		$chart.append($toolTip);

		var tooltipText = '',
			value = $el[0].getAttribute('ct:value');

		if (value) {
			value = '<span class="chartist-tooltip-value">' + value + '</span>';
			tooltipText += value;
		}

		if(tooltipText) {
			$toolTip[0].innerHTML = tooltipText;
			var box = $chart[0].getBoundingClientRect();
			var top = $el.offset().top - box.top - window.pageYOffset - $toolTip.height() - 25;
			var left = $el.offset().left - box.left - window.pageXOffset - $toolTip.width()/2 + 2;

			$toolTip[0].style.top = top + 'px';
			$toolTip[0].style.left = left + 'px';
			$toolTip.addClass('tooltip-show');
		}
	})
}