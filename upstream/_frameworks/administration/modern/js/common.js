/*$.fn.oneAnimationEnd=function(fn){
	this.one('animationend webkitanimationend', fn);
    if (!Modernizr.csstransitions) this.trigger('animationend');
	return this
}*/

var animateEvent='animationend webkitanimationend';

$.fn.oneAnimationEnd=function(fn){
    var el=this;
    el.on(animateEvent, function f(e){
        $(this).off(animateEvent, f);
        fn.call(this, e);
    });
    if (!window.AnimationEvent && !window.WebKitAnimationEvent) {
        setTimeout(function(){el.trigger('animationend')},10)
    }
	return this
}

$.fn.oneTransEndM=function(fn, prop){
    //"transitionend webkitTransitionEnd oTransitionEnd otransitionend MSTransitionEnd"
	var trans=Modernizr.csstransitions;
	//console.log(typeof prop);
	return trans ? this.on('webkittransitionend transitionend', function fu(e){
		if ((prop && e.originalEvent.propertyName.replace(/-webkit-|-moz-|-ms-/, '')!=prop) || e.target!=this) return;
		//console.log(e.originalEvent.propertyName, prop, e.target);
		$(this).off('webkittransitionend transitionend', fu)
		fn.call(this, e)
	}) : this.each(fn);
	return this
}

var transEvent='transitionend webkitTransitionEnd';
$.fn.oneTransEnd=function(fn, prop){
	var el=this;
    el.on(transEvent, function f(e){
        var eProp=e.propertyName=e.originalEvent.propertyName;
        if (!eProp || new RegExp(prop||'', 'i').test(eProp)) {
            $(this).off(transEvent, f);
            fn.call(this, e);
        }
    });
	if (!window.TransitionEvent && !window.WebKitTransitionEvent) {
        setTimeout(function(){el.trigger('transitionend');},10)
    }
	return this
}

inViewport = function(element, options) {
    var settings = {
        threshold  : 0,
        container  : window.mainContentBlock||window
    };
    if(options) {
        $.extend(settings, options);
    }
	if (!element.getBoundingClientRect) return true;
		settings.threshold>>=0;
		var elRect=element.getBoundingClientRect(), top=0, left=0,
			bottom=window.innerHeight||$window.height(), right=window.innerWidth||$window.width();
        if (settings.container) {
			var contRect=settings.container.getBoundingClientRect();
			top = Math.max(0, contRect.top);
			left = Math.max(0, contRect.left);
			bottom = Math.min(bottom, contRect.bottom);
			right = Math.min(right, contRect.right);
		}
    return top   < elRect.bottom + settings.threshold
            && left  < elRect.right + settings.threshold
			&& bottom> elRect.top - settings.threshold
			&& right > elRect.left - settings.threshold;
};

$.fn.focusEl = function(options){
    if(!isMobileBrowserIOS){
        $(this).focus();
    };
    return this
};