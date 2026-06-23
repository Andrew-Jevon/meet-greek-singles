(function ($) {
	var
	_defaults = {
		className: 'autosizejs',
		append: '',
		callback: false,
        callbackResize: false,
		callbackSend: false,
        isSetScrollHeight: true,
		contenteditable: false
	},
	_hidden = 'hidden',
	_borderBox = 'border-box',
	_lineHeight = 'lineHeight',
	_supportsScrollHeight,

	_copy = '<div tabindex="-1" role="textbox" aria-multiline="true" contenteditable="true"  style="position:absolute; top:-999px; left:0; right:auto; bottom:auto; border:0; -moz-box-sizing:content-box; -webkit-box-sizing:content-box; box-sizing:content-box; word-wrap:break-word; height:0 !important; min-height:0 !important; overflow:hidden;"></div>',
	_copyStyle = [
		'fontFamily',
		'fontSize',
		'fontWeight',
		'fontStyle',
		'letterSpacing',
		'textTransform',
		'wordSpacing',
		'textIndent'
	],
	_mirrored,
	_mirror = $(_copy).data('autosize_div', true)[0];

	_mirror.style.lineHeight = '99px';
	if ($(_mirror).css(_lineHeight) === '99px') {
		_copyStyle.push(_lineHeight);
	}
	_mirror.style.lineHeight = '';

	$.fn.autosize_editable = function (options) {
		options = $.extend({}, _defaults, options || {});

		if (_mirror.parentNode !== document.body) {
			$(document.body).append(_mirror);
			_mirror.innerHTML = '<br><br><br>';//"\n\n\n";
			_mirror.scrollTop = 9e4;
			_supportsScrollHeight = _mirror.scrollHeight === _mirror.scrollTop + _mirror.clientHeight;
		}

		return this.each(function(){
			var
			ta = this,
			$ta = $(ta),
			minHeight,
			_active,
			resize,
			boxOffset = 0,
			callback = $.isFunction(options.callback),
            callbackResize = $.isFunction(options.callbackResize);
			if ($ta.data('autosize_div')) {
				// exit if autosize has already been applied, or if the textarea is the _mirror element.
				return;
			}

			if ($ta.css('box-sizing') === _borderBox || $ta.css('-moz-box-sizing') === _borderBox || $ta.css('-webkit-box-sizing') === _borderBox){
				boxOffset = $ta.outerHeight() - $ta.height();
			}

			minHeight = Math.max(parseInt($ta.css('minHeight'), 10) - boxOffset, $ta.height());

			resize = ($ta.css('resize') === 'none' || $ta.css('resize') === 'vertical') ? 'none' : 'horizontal';

			$ta.css({
				overflow: _hidden,
				overflowY: _hidden,
				wordWrap: 'break-word',
				resize: resize
			}).data('autosize_div', true);

			function _initMirror() {
				_mirrored = ta;
				_mirror.className = options.className;
				$.each(_copyStyle, function(i, val){
					_mirror.style[val] = $ta.css(val);

				});
			}

			// Using mainly bare JS in this function because it is going
			// to fire very often while typing, and needs to very efficient.
			function _adjust(isCallbackResize) {
                isCallbackResize=isCallbackResize||false;
				var height, overflow, original, resized,
					defaultHeight=false;
				if (_mirrored !== ta) {
					_initMirror();
					defaultHeight=parseInt($ta.css('minHeight'), 10);
					if (isNaN(defaultHeight)){
						defaultHeight=false;
					}
				}

				// the _active flag keeps IE from tripping all over itself.  Otherwise
				// actions in the _adjust function will cause IE to call _adjust again.
				if (!_active) {

					_active = true;

					_mirror.innerHTML = ta.innerHTML + options.append;
					_mirror.style.overflowY = ta.style.overflowY;
					original = parseInt(ta.style.height,10);

					// Update the width in case the original textarea width has changed
					// A floor of 0 is needed because IE8 returns a negative value for hidden textareas, raising an error.
					_mirror.style.width = Math.max($ta.width(), 0) + 'px';

					if (_supportsScrollHeight && options.isSetScrollHeight) {
						height = _mirror.scrollHeight;
					} else { // IE6 & IE7
						_mirror.scrollTop = 0;
						_mirror.scrollTop = 9e4;
						height = _mirror.scrollTop;
					}

					var maxHeight = parseInt($ta.css('maxHeight'), 10);
					// Opera returns '-1px' when max-height is set to 'none'.
					maxHeight = maxHeight && maxHeight > 0 ? maxHeight : 9e4;
					if (height > maxHeight) {
						height = maxHeight;
						overflow = 'scroll';
					} else if (height < minHeight) {
						height = minHeight;
					}
					height += boxOffset;
					if(defaultHeight !== false && height > defaultHeight){
						height=defaultHeight;
					}
					ta.style.overflowY = overflow || _hidden;

					if (resized=(original!==height)) {
						//ta.blur();
						ta.style.height = height + 'px';
						//$(ta).closest('.comment_container_textarea')[height>=100?'addClass':'removeClass']('bl_textarea_100');
						//ta.focus();
						if (callback) {
							options.callback.call(ta,ta,height);
						}
					}
                    if (isCallbackResize===true&&callbackResize) {
                        options.callbackResize.call(ta,ta,height);
                    }

					// This small timeout gives IE a chance to draw it's scrollbar
					// before _adjust can be run again (prevents an infinite loop).
					setTimeout(function () {
						if (resized && !options.noscroll) ta.scrollTop=0;
						_active = false;
					}, 1);
				}
			}

			//Filter out everything except simple text and allowable HTML elements
			ta.addEventListener('paste', function(e){
				var data = e.clipboardData.getData('text/plain');
				//var regex = /<(?!(\/\s*)?(br)[>,\s])([^>])*>/g;
				//data = data.replace(regex, '');
				// Fix - allow insert HTML code as encoded entities
				var data = $('<div>').text(data).html();
				data = data.replace(/\n/g, '<br>');

				document.execCommand('insertHTML', false, data);
				e.preventDefault();
			});

			function _unwrap(el, target) {
				if(!target)target=el.parentNode;
				while(el.firstChild){
					target.appendChild(el.firstChild);
				}
				el.parentNode.removeChild(el);
			}
			// ta.addEventListener('DOMNodeInserted', function(e) {
            //     console.log('ta.addEventListener(DOMNodeInserted) run');
			// 	if (e.target && e.target.tagName!=undefined
			// 		&& e.target.tagName!='BR'
			// 		&& (e.target.tagName!='IMG'
			// 			||(e.target.tagName=='IMG' && !e.target.classList.contains('emoji')))
			// 		&& (e.target.tagName!='SPAN'
			// 			||(e.target.tagName=='SPAN' && !e.target.classList.contains('im_audio_message_send_play')))
			// 		) {
            //          console.log('DOMNodeInserted event here');
			// 		_unwrap(e.target);
			// 	}
			// })

			ta.addEventListener('keydown', function(e){
				var key=e.keyCode||e.which,d=document;
				if (key===8) {
					var t=this.innerText.replace(/\n/g, '');
					if(!t&&!$ta.find('.emoji')[0]&&$ta.find('.im_audio_message_send_play')[0]){
						e.preventDefault();
					}
				} else if(key===13){
					var el=this;

					if(d.queryCommandSupported("defaultParagraphSeparator"))d.execCommand("defaultParagraphSeparator", false, "");
					if(d.queryCommandSupported('insertHTML'))d.execCommand('insertHTML', false, "");
					if(d.queryCommandSupported("insertBrOnReturn"))d.execCommand("insertBrOnReturn", false, "");

					if (isMobileSite) {
						insertCaretDivContentEditable(el);
					} else {
						var submitOnEnter=!/submitOnEnter=0/.test(document.cookie),
							callbackSend=$.isFunction(options.callbackSend);
						if (submitOnEnter && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
							callbackSend && options.callbackSend(el);
						} else if (e.ctrlKey) {
							if (submitOnEnter){
								insertCaretDivContentEditable(this);
							} else {
								callbackSend && options.callbackSend(el);
							}
						}
					}
					e.preventDefault();
				}
			})


			function _setCaret() {
				$ta.data('caret-position', divGetCaretRange())
			}

			$ta.on('input propertychange', _adjust)
			.on('blur', function(){
				var $el=$(this),
					v=trim($el.text());
				if (!v&&!$el.find('.emoji, .im_audio_message_send_play')[0]) {
					$el.empty();
				}
				_setCaret();
			})
			.on('keydown mousedown', function(){//Add <br> last child - touchstart
				if (!this.lastChild || this.lastChild.nodeName.toLowerCase() != "br") {
					this.appendChild(document.createElement('br'));
				}
			})
			.on('mouseup', _setCaret)// touchend
			.on('keyup', function(e){
				_setCaret();
				if (window.getSelection) {
					var $smile, sel, startIndex, endIndex, smile, src, id, emoji;
					for (var search in smilesListDefault) {
						if(this.innerHTML.indexOf(search) !== -1) {
							//Replace smile code
							sel = window.getSelection();
							if (!sel.focusNode || ! sel.focusNode.nodeValue) {// Nothing focused
								continue;
							}
							startIndex = sel.focusNode.nodeValue.indexOf(search);
							endIndex = startIndex + search.length;
							if (startIndex === -1) { // search not found
								continue;
							}
							var range = document.createRange();
							range.setStart(sel.focusNode, startIndex);
							range.setEnd(sel.focusNode, endIndex);
							range.deleteContents(); //Delete search text

							/*$smile=$jq('#smile_bl_tmpl').find('.emoji[data-id="'+smilesListDefault[search]+'"]');

							emoji = document.createElement('img');
							emoji.src=$smile.data('src');
							emoji.classList.add('emoji');
							emoji.dataset.alias='{emoji:'+id+'}';
							emoji.dataset.id=id;
							emoji.dataset.src=$smile.data('src');

							range.insertNode(emoji);
							range.setStartAfter(emoji);
							sel.removeAllRanges(); // Chrome fix
							sel.addRange(range);
							*/

							$smile=$jq('#smile_bl_tmpl').find('.emoji[data-id="'+smilesListDefault[search]+'"]').clone();
							smileInsertManual($smile, $ta);
						}
					}
				}
			})
			.on('placeholder', function(e){//Change placeholder
				var $el=$(this),
					pl=$el.data('placeholder'),
					plNew=$el.data('placeholderNew');
				$el.attr('data-placeholder-new', '').data('placeholderNew', '');
				if(pl == plNew)return;
				$el.attr('data-placeholder', plNew).data('placeholder', plNew);
			})
			.on('disabled', function(e){//Change disabled
				var $el=$(this),
					disabled=$el.data('disabled');
				$el[disabled?'addClass':'removeClass']('disabled');
				$el.closest('.field_comment,.field_comment_wrap')[disabled?'addClass':'removeClass']('disabled');
				$el.attr('contenteditable', !disabled);
			})
			.on('clear-caret-position', function(e){
				$ta.data('caret-position', null)
			})
			.on('autosize', function(e,callback){//Allow for manual triggering if needed
				_active = false;
				_adjust();
                if($.isFunction(callback)){
                    callback();
                }
			})

			$win.on('resize', function(){
				_active = false;
                _adjust(true);
			})

			_adjust();
		})
	}
}(window.jQuery || window.Zepto));
