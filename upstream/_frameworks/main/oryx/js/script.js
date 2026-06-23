var transEvent='transitionend webkitTransitionEnd';
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

$.fn.oneTransEnd=function(fn, prop){
	var el=this;
    el.on(transEvent, function f(e){
        var eProp=e.propertyName;
		if(e.originalEvent!=undefined){
			eProp=e.originalEvent.propertyName;
		}
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

function addChildrenLoader($btn, notHidden){
    notHidden=defaultFunctionParamValue(notHidden, true);
    var $iconFa = $btn.find('.icon_fa, .icon, .loader_wrap');
    if (notHidden) {
        $iconFa = $iconFa.not(':hidden');
    }
    if($iconFa[0]){
        $iconFa.addChildrenLoader();
    }else{
        $btn.addChildrenLoader();
    }
}

function addLoaderCheckDevice($btn){
    if(notLoaderIos)return false;
    addChildrenLoader($btn)
}

function removeChildrenLoader($btn){
    var $iconFa = $btn.find('.icon_fa, .icon');//.not(':hidden');
    if($iconFa[0]){
        $iconFa.removeChildrenLoader();
    }else{
        $btn.removeChildrenLoader();
    }
}