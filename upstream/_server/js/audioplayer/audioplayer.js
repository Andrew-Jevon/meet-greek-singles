(function(window, undefined) {

'use strict';

var AudioPlayer = (function() {
    var
    docTitle = document.title,
    player,
    playBtn,
    playSvg,
    playSvgPath,
    prevBtn,
    nextBtn,
    closeBtn,
    plBtn,
    repeatBtn,
    volumeBtn,
    progressBar, preloadBar,
    curTime, durTime, trackTitle,
    audio,
    index = 0,
    id = 0,
    playList,
    volumeBar,
    wheelVolumeValue = 0,
    volumeLength,
    repeating = false,
    seeking = false,
    seekingVol = false,
    rightClick = false,
    apActive = false,
    // playlist vars
    pl,
    plUl,
    plLi,
    tplList =
            '<li id="pl-list-{id}" class="pl-list" data-track="{count}">'+
              '<div class="pl-list__track">'+
                '<div class="pl-list__icon"></div>'+
                '<div class="pl-list__eq">'+
                  '<div class="eq">'+
                    '<div class="eq__bar"></div>'+
                    '<div class="eq__bar"></div>'+
                    '<div class="eq__bar"></div>'+
                  '</div>'+
                '</div>'+
              '</div>'+
              '<div class="pl-list__title">{title}</div>'+
              '<button class="pl-list__remove">'+
                '<svg fill="#000000" height="20" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg">'+
                    '<path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>'+
                    '<path d="M0 0h24v24H0z" fill="none"/>'+
                '</svg>'+
              '</button>'+
            '</li>',
    //Settings
    settings = {
        volume        : 0.7,
        changeDocTitle: true,
        confirmClose  : true,
        autoPlay      : false,
        buffered      : true,
        notification  : true,
        playSeek      : false,
        playList      : [],
        index         : 0,
        id            : 0
    };

    function init(options) {

        if(!('classList' in document.documentElement)) {
            return false;
        }

        player = document.getElementById('player_song');

        settings = extend(settings, options);

        index = settings.index;
        id = settings.id;
        if(apActive || player === null) {
            if (settings.playSeek) {
                play(id);
            }

            return AudioPlayer;
        }

        // get player elements
        playBtn        = player.querySelector('.ap__controls--toggle');
        playSvg        = playBtn.querySelector('.icon-play');
        playSvgPath    = playSvg.querySelector('path');
        prevBtn        = player.querySelector('.ap__controls--prev');
        nextBtn        = player.querySelector('.ap__controls--next');
        repeatBtn      = player.querySelector('.ap__controls--repeat');
        volumeBtn      = player.querySelector('.volume-btn');
        plBtn          = player.querySelector('.ap__controls--playlist');
        curTime        = player.querySelector('.track__time--current');
        durTime        = player.querySelector('.track__time--duration');
        trackTitle     = player.querySelector('.track__title');
        progressBar    = player.querySelector('.progress__bar');
        preloadBar     = player.querySelector('.progress__preload');
        volumeBar      = player.querySelector('.volume__bar');
        closeBtn       = player.querySelector('.icon-close-ap');

        playList = settings.playList;

        playBtn.addEventListener('click', playToggle, false);
        volumeBtn.addEventListener('click', volumeToggle, false);

		if (isMobileIOS) {
			player.querySelector('.volume-container-bl').style.display = 'none';
			volumeBtn.style.display = 'none';
			player.querySelector('.volume').style.display = 'none';
		}

        closeBtn.addEventListener('click', function(){
            close();
        }, false);

        //repeatBtn.addEventListener('click', repeatToggle, false);

        progressBar.closest('.progress-container').addEventListener('mousedown', handlerBar, false);
        progressBar.closest('.progress-container').addEventListener('mousemove', seek, false);

        document.documentElement.addEventListener('mouseup', seekingFalse, false);

        volumeBar.closest('.volume').addEventListener('mousedown', handlerVol, false);
        volumeBar.closest('.volume').addEventListener('mousemove', setVolume);
        volumeBar.closest('.volume').addEventListener(wheel(), setVolume, false);


        changeControls();

        prevBtn.addEventListener('click', prev, false);
        nextBtn.addEventListener('click', next, false);

        apActive = true;

        // Create playlist
        renderPL();

        //plBtn.addEventListener('click', plToggle, false);

        // Create audio object
        audio = new Audio();

        /* Volume */
        var _muted=$.cookie('_ap_muted');
        if(_muted == undefined || isMobileIOS){
            _muted = 0;
        }
        _muted *=1;

        var _volume=_apGetVolume(), _volumeBar=_volume;
        if(_muted || !_volume){
            volumeBtn.classList.add('has-muted');
            audio.muted=true;
            _volumeBar=0;
        }
        audio.volume = _volume;

        console.log('AP volume start:', _muted, _volume);
        /* Volume */

        audio.preload = 'auto';

        audio.addEventListener('error', errorHandler, false);
        audio.addEventListener('timeupdate', timeUpdate, false);
        audio.addEventListener('ended', doEnd, false);
        audio.addEventListener('loadstart', function(){
            console.log('AP loadstart:', id);
            clProfileSongs.increasePlays(id);
        }, false);

        volumeBar.style.height = _volumeBar * 100 + '%';
        volumeLength = volumeBar.css('height');

        if(settings.confirmClose) {
            window.addEventListener("beforeunload", beforeUnload, false);
        }

        if(isEmptyList()) {
            return false;
        }

        audio.src = playList[id].file;
        trackTitle.innerHTML = playList[id].title;

        if(settings.autoPlay) {
            autoPlay(id)
        }

        return AudioPlayer;
    }

    function _apGetVolume(){
		if (isMobileIOS) {
			return 1;
		}
        var _volume=$.cookie('_ap_mute_volume');
        if(_volume == undefined){
            _volume = settings.volume;
        }
        return _volume*1;
    }

    function close(){
        playToggle(true);
        player.classList.remove('to_show');
    }

    function lengthPlayList(){
        return Object.keys(playList).length;
    }

    function changeControls(){
        var $btnNext=$(nextBtn),
            $btnPrev=$(prevBtn);
        if (lengthPlayList() > 1) {
            $btnNext.show();
            $btnPrev.show();
        } else {
            $btnNext.hide();
            $btnPrev.hide();
        }
        console.log('AP:', playList, Object.keys(playList).length);
    }

    function isActive(){
        return apActive;
    }

    function getCurrentTrack(){
        return id;
    }

    function getAudio(){
        return audio;
    }

    function changeStatusStop(){
        $('.list_songs_item_wrap').removeClass('play_pause');
    }

    function changeStatusPlay(id){
        changeStatusStop();
        $('#list_songs_item_wrap_'+id).addClass('play_pause');
        $('#wall_song_image_'+id).addClass('play_pause');
    }

    function autoPlay(id){
        changeStatusPlay(id);

        audio.play();
        playBtn.classList.add('is-playing');
        playSvgPath.setAttribute('d', playSvg.getAttribute('data-pause'));

        $('#pl-list-'+id).addClass('pl-list--current');
        //plLi[id].classList.add('pl-list--current');
        notify(playList[id].title, {
            icon: playList[id].icon,
            body: 'Now playing'
        })
    }

    function changeDocumentTitle(title) {
        if(settings.changeDocTitle) {
            if(title) {
                document.title = title;
            } else {
                document.title = docTitle;
            }
        }
    }

    function beforeUnload(evt) {
        if(!audio.paused) {
            var message = 'Music still playing';
            evt.returnValue = message;
            return message;
        }
    }

    function errorHandler(evt) {
        if(isEmptyList()) {
            return;
        }
        var mediaError = {
            '1': 'MEDIA_ERR_ABORTED',
            '2': 'MEDIA_ERR_NETWORK',
            '3': 'MEDIA_ERR_DECODE',
            '4': 'MEDIA_ERR_SRC_NOT_SUPPORTED'
        };
        audio.pause();
        curTime.innerHTML = '--';
        durTime.innerHTML = '--';
        progressBar.style.width = 0;
        preloadBar.style.width = 0;
        playBtn.classList.remove('is-playing');
        playSvgPath.setAttribute('d', playSvg.getAttribute('data-play'));

        var $li=$('#pl-list-'+id);
        if ($li[0]) {
            $li.removeClass('pl-list--current');
        }
        //plLi[index] && plLi[index].classList.remove('pl-list--current');

        changeDocumentTitle();
        throw new Error('Houston we have a problem: ' + mediaError[evt.target.error.code]);
    }

    /* Update PL */
    function updatePL(addList) {
        if(!apActive) {
            return 'Player is not yet initialized';
        }
        if(!Array.isArray(addList)) {
            return;
        }
        if(addList.length === 0) {
            return;
        }

        var html  = [];
        playList.push.apply(playList, addList);
        for (var key in addList) {
            var item=addList[key];
        //addList.forEach(function(item) {
            html.push(
                //tplList.replace('{count}', count++).replace('{title}', item.title)
                tplList.replace('{count}', item['id'])
                       .replace('{title}', item.title ? item.title : 'Unknown')
                       .replace('{id}', item['id'])
            );
        //});
        }
        // If exist empty message
        if(plUl.querySelector('.pl-list--empty')) {
            plUl.removeChild(pl.querySelector('.pl-list--empty') );
            audio.src = playList[id].file;
            trackTitle.innerHTML = playList[id].title;
        }
        // Add song into playlist
        plUl.insertAdjacentHTML('beforeEnd', html.join(''));
        plLi = pl.querySelectorAll('li');
    }

    /* PlayList methods  */
    function renderPL() {
        var html = [];

        for (var key in playList) {
            var item=playList[key];
            html.push(
                //tplList.replace('{count}', i).replace('{title}', item.title)
                tplList.replace('{count}', item['id'])
                       .replace('{title}', item.title ? item.title : 'Unknown')
                       .replace('{id}', item['id'])
            );
        }

        pl = create('div', {
            'className': 'pl-container',
            'id': 'pl',
            'innerHTML': '<ul class="pl-ul">' + (!isEmptyList() ? html.join('') : '<li class="pl-list--empty">PlayList is empty</li>') + '</ul>'
        });

        player.parentNode.insertBefore(pl, player.nextSibling);

        plUl = pl.querySelector('.pl-ul');
        plLi = plUl.querySelectorAll('li');

        pl.addEventListener('click', listHandler, false);
    }

    function listHandler(evt) {
        evt.preventDefault();

        if(evt.target.matches('.pl-list__title')) {
            var current = parseInt(evt.target.closest('.pl-list').getAttribute('data-track'), 10);
            if(id !== current) {
                id = current;
                play(current);
            } else {
                playToggle();
            }
        } else {
          if(!!evt.target.closest('.pl-list__remove')) {
                var parentEl = evt.target.closest('.pl-list');
                var isDel = parseInt(parentEl.getAttribute('data-track'), 10);

                playList.splice(isDel, 1);
                parentEl.closest('.pl-ul').removeChild(parentEl);

                plLi = pl.querySelectorAll('li');

                [].forEach.call(plLi, function(el, i) {
                    el.setAttribute('data-track', i);
                });

                if(!audio.paused) {
                    if(isDel === id) {
                        play(id);
                    }
                } else {
                    if(isEmptyList()) {
                        clearAll();
                    } else {
                        if(isDel === id) {
                            /* ??????????????? */
                            if(isDel > playList.length - 1) {
                                index -= 1;
                            }
                            audio.src = playList[index].file;
                            trackTitle.innerHTML = playList[index].title;
                            progressBar.style.width = 0;
                            /* ??????????????? */
                        }
                    }
                }
                /* ??????????????? */
                if(isDel < index) {
                    index--;
                }
                /* ??????????????? */
            }
        }
    }

    function plActive() {
        var $li=$('#pl-list-'+id);
        if(audio.paused) {
            //if ($li[0]) {
                $li.removeClass('pl-list--current');
            //}
            //plLi[index].classList.remove('pl-list--current');
            return;
        }

        //var current = index;
        //var current = id;
        for(var i = 0, len = plLi.length; len > i; i++) {
            plLi[i].classList.remove('pl-list--current');
        }
        //if ($li[0]) {
            $li.addClass('pl-list--current');
        //}
        //plLi[current].classList.add('pl-list--current');
    }


    /* Player methods */
    function play(idNew) {
        if(isEmptyList()) {
            return clearAll();
        }

        id = idNew;
        changeStatusPlay(id);

        console.log('AP: Play TRACK',id);
        //index = (currentIndex + playList.length) % playList.length;
        //console.log('PLAY index', index);
        audio.src = playList[id].file;
        trackTitle.innerHTML = playList[id].title;

        // Change document title
        changeDocumentTitle(playList[id].title);

        // Audio play
        audio.play();

        // Show notification
        notify(playList[id].title, {
            icon: playList[id].icon,
            body: 'Now playing',
            tag: 'music-player'
        });

        // Toggle play button
        playBtn.classList.add('is-playing');
        playSvgPath.setAttribute('d', playSvg.getAttribute('data-pause'));

        // Set active song playlist
        plActive();
    }


    function nextTrack(id, prev) {
        prev=prev||false;
        var arr = Object.keys(playList), indx;
        if (prev) {
            indx = arr.indexOf(id)-1;
        } else {
            indx = arr.indexOf(id)+1;
        }
        if (prev) {
            if (indx<0) {
                return playList[arr[arr.length - 1]]['id'];
            }
        } else {
            if (indx > (arr.length - 1)) {
                return playList[arr[0]]['id'];
            }
        }
        return playList[arr[indx]]['id'];
    }

    function prev() {
        play(nextTrack(id));
    }

    function next() {
        play(nextTrack(id, true));
    }

    function isEmptyList() {
        return $.isEmptyObject(playList);
        //return playList.length === 0;
    }

    function clearAll() {
        audio.pause();
        audio.src = '';
        trackTitle.innerHTML = 'queue is empty';
        curTime.innerHTML = '--';
        durTime.innerHTML = '--';
        progressBar.style.width = 0;
        preloadBar.style.width = 0;
        playBtn.classList.remove('is-playing');
        playSvgPath.setAttribute('d', playSvg.getAttribute('data-play'));
        if(!plUl.querySelector('.pl-list--empty')) {
            plUl.innerHTML = '<li class="pl-list--empty">PlayList is empty</li>';
        }
        changeDocumentTitle();
    }

    function playToggle(stop) {
        if(isEmptyList()) {
            return;
        }
        if (typeof stop == 'undefined' || typeof stop != 'boolean') {
            stop=false;
        }

        if(audio.paused && !stop) {
            if(audio.currentTime === 0) {
                notify(playList[id].title, {
                    icon: playList[id].icon,
                    body: 'Now playing'
                });
            }
            changeDocumentTitle(playList[id].title);

            audio.play();

            playBtn.classList.add('is-playing');
            playSvgPath.setAttribute('d', playSvg.getAttribute('data-pause'));

            changeStatusPlay(id);
        } else {
            changeDocumentTitle();
            audio.pause();
            playBtn.classList.remove('is-playing');
            playSvgPath.setAttribute('d', playSvg.getAttribute('data-play'));
            changeStatusStop();
        }
        plActive();
    }

    function volumeToggle() {
        var _volume;
        if(audio.muted) {
            if(parseInt(volumeLength, 10) === 0) {
                var _volume=_apGetVolume();
                if (!_volume){
                    _volume=settings.volume;
                }
                volumeBar.style.height = _volume * 100 + '%';
                audio.volume = _volume;
            } else {
                volumeBar.style.height = volumeLength;
            }
            audio.muted = false;
            volumeBtn.classList.remove('has-muted');
        } else {
            audio.muted = true;
            volumeBar.style.height = 0;
            volumeBtn.classList.add('has-muted');
        }
        console.log('AP volume set toggle:', audio.muted);
        $.cookie('_ap_muted', audio.muted?1:0, {path:'/'});

    }

    function repeatToggle() {
        if(repeatBtn.classList.contains('is-active')) {
            repeating = false;
            repeatBtn.classList.remove('is-active');
        } else {
            repeating = true;
            repeatBtn.classList.add('is-active');
        }
    }

    function plToggle() {
        plBtn.classList.toggle('is-active');
        pl.classList.toggle('h-show');
    }

    function timeUpdate() {
        if(audio.readyState === 0 || seeking) return;

        var barlength = Math.round(audio.currentTime * (100 / audio.duration));
        progressBar.style.width = barlength + '%';

        var
        curMins = Math.floor(audio.currentTime / 60),
        curSecs = Math.floor(audio.currentTime - curMins * 60),
        mins = Math.floor(audio.duration / 60),
        secs = Math.floor(audio.duration - mins * 60);
        (curSecs < 10) && (curSecs = '0' + curSecs);
        (secs < 10) && (secs = '0' + secs);

        curTime.innerHTML = curMins + ':' + curSecs;
        durTime.innerHTML = mins + ':' + secs;

        if(settings.buffered) {
            var buffered = audio.buffered;
            if(buffered.length) {
                var loaded = Math.round(100 * buffered.end(0) / audio.duration);
                preloadBar.style.width = loaded + '%';
            }
        }
    }

    /* TODO shuffle */
    function shuffle() {
        if(shuffle) {
            index = Math.round(Math.random() * playList.length);
        }
    }

    function doEnd() {
        play(nextTrack(id, true));
		/*var arr = Object.keys(playList);
        if(id === playList[arr[arr.length - 1]]['id']) {
            if(!repeating) {
                audio.pause();
                plActive();
                playBtn.classList.remove('is-playing');
                playSvgPath.setAttribute('d', playSvg.getAttribute('data-play'));

                changeStatusStop();
                return;
            } else {
                var idNew=playList[arr[0]]['id'];
                play(idNew);
                play(nextTrack(id));
            }
        } else {
            play(nextTrack(id));
        }*/
    }

  function moveBar(evt, el, dir) {
    var value;
    if(dir === 'horizontal') {
      value = Math.round( ((evt.clientX - el.offset().left) + window.pageXOffset)  * 100 / el.parentNode.offsetWidth);
      el.style.width = value + '%';
      return value;
    }
    else {
      if(evt.type === wheel()) {
        value = parseInt(volumeLength, 10);
        var delta = evt.deltaY || evt.detail || -evt.wheelDelta;
        value = (delta > 0) ? value - 10 : value + 10;
      }
      else {
        var offset = (el.offset().top + el.offsetHeight) - window.pageYOffset;
        value = Math.round((offset - evt.clientY));
      }
      if(value > 100) value = wheelVolumeValue = 100;
      if(value < 0) value = wheelVolumeValue = 0;
      volumeBar.style.height = value + '%';
      return value;
    }
  }

  function handlerBar(evt) {
    rightClick = (evt.which === 3) ? true : false;
    seeking = true;
    !rightClick && progressBar.classList.add('progress__bar--active');
    seek(evt);
  }

  function handlerVol(evt) {
    rightClick = (evt.which === 3) ? true : false;
    seekingVol = true;
    setVolume(evt);
  }

  function seek(evt) {
    evt.preventDefault();
    if(seeking && rightClick === false && audio.readyState !== 0) {
      window.value = moveBar(evt, progressBar, 'horizontal');
    }
  }

  function seekingFalse() {
    if(seeking && rightClick === false && audio.readyState !== 0) {
      audio.currentTime = audio.duration * (window.value / 100);
      progressBar.classList.remove('progress__bar--active');
    }
    seeking = false;
    seekingVol = false;
  }

  function setVolume(evt) {
    evt.preventDefault();
    volumeLength = volumeBar.css('height');
    if(seekingVol && rightClick === false || evt.type === wheel()) {
      var value = moveBar(evt, volumeBar.parentNode, 'vertical') / 100;
      if(value <= 0) {
        audio.volume = 0;
        audio.muted = true;
        volumeBtn.classList.add('has-muted');
        value=0;
      }
      else {
        if(audio.muted) audio.muted = false;
        audio.volume = value;
        volumeBtn.classList.remove('has-muted');
      }
      console.log('AP volume set:', value, audio.muted);
      $.cookie('_ap_muted', audio.muted?1:0, {path:'/'});
      $.cookie('_ap_mute_volume', value, {path:'/'});
    }
  }

  function notify(title, attr) {
    if(!settings.notification) {
      return;
    }
    if(window.Notification === undefined) {
      return;
    }
    attr.tag = 'AP music player';
    window.Notification.requestPermission(function(access) {
      if(access === 'granted') {
        var notice = new Notification(title.substr(0, 110), attr);
        setTimeout(notice.close.bind(notice), 5000);
      }
    });
  }

    /* Destroy method. Clear All */
    function destroy() {
    if(!apActive) return;

    if(settings.confirmClose) {
      window.removeEventListener('beforeunload', beforeUnload, false);
    }

    playBtn.removeEventListener('click', playToggle, false);
    volumeBtn.removeEventListener('click', volumeToggle, false);
    repeatBtn.removeEventListener('click', repeatToggle, false);
    plBtn.removeEventListener('click', plToggle, false);

    progressBar.closest('.progress-container').removeEventListener('mousedown', handlerBar, false);
    progressBar.closest('.progress-container').removeEventListener('mousemove', seek, false);
    document.documentElement.removeEventListener('mouseup', seekingFalse, false);

    volumeBar.closest('.volume').removeEventListener('mousedown', handlerVol, false);
    volumeBar.closest('.volume').removeEventListener('mousemove', setVolume);
    volumeBar.closest('.volume').removeEventListener(wheel(), setVolume);
    document.documentElement.removeEventListener('mouseup', seekingFalse, false);

    prevBtn.removeEventListener('click', prev, false);
    nextBtn.removeEventListener('click', next, false);

    audio.removeEventListener('error', errorHandler, false);
    audio.removeEventListener('timeupdate', timeUpdate, false);
    audio.removeEventListener('ended', doEnd, false);

    // Playlist
    pl.removeEventListener('click', listHandler, false);
    pl.parentNode.removeChild(pl);

    audio.pause();
    apActive = false;
    index = 0;

    playBtn.classList.remove('is-playing');
    playSvgPath.setAttribute('d', playSvg.getAttribute('data-play'));
    volumeBtn.classList.remove('has-muted');
    plBtn.classList.remove('is-active');
    repeatBtn.classList.remove('is-active');

    // Remove player from the DOM if necessary
    // player.parentNode.removeChild(player);
  }


/**
 *  Helpers
 */
  function wheel() {
    var wheel;
    if ('onwheel' in document) {
      wheel = 'wheel';
    } else if ('onmousewheel' in document) {
      wheel = 'mousewheel';
    } else {
      wheel = 'MozMousePixelScroll';
    }
    return wheel;
  }

  function extend(defaults, options) {
    for(var name in options) {
      if(defaults.hasOwnProperty(name)) {
        defaults[name] = options[name];
      }
    }
    return defaults;
  }
  function create(el, attr) {
    var element = document.createElement(el);
    if(attr) {
      for(var name in attr) {
        if(element[name] !== undefined) {
          element[name] = attr[name];
        }
      }
    }
    return element;
  }

  Element.prototype.offset = function() {
    var el = this.getBoundingClientRect(),
    scrollLeft = window.pageXOffset || document.documentElement.scrollLeft,
    scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    return {
      top: el.top + scrollTop,
      left: el.left + scrollLeft
    };
  };

  Element.prototype.css = function(attr) {
    if(typeof attr === 'string') {
      return getComputedStyle(this, '')[attr];
    }
    else if(typeof attr === 'object') {
      for(var name in attr) {
        if(this.style[name] !== undefined) {
          this.style[name] = attr[name];
        }
      }
    }
  };

  // matches polyfill
  window.Element && function(ElementPrototype) {
      ElementPrototype.matches = ElementPrototype.matches ||
      ElementPrototype.matchesSelector ||
      ElementPrototype.webkitMatchesSelector ||
      ElementPrototype.msMatchesSelector ||
      function(selector) {
          var node = this, nodes = (node.parentNode || node.document).querySelectorAll(selector), i = -1;
          while (nodes[++i] && nodes[i] != node);
          return !!nodes[i];
      };
  }(Element.prototype);

  // closest polyfill
  window.Element && function(ElementPrototype) {
      ElementPrototype.closest = ElementPrototype.closest ||
      function(selector) {
          var el = this;
          while (el.matches && !el.matches(selector)) el = el.parentNode;
          return el.matches ? el : null;
      };
  }(Element.prototype);

/**
 *  Public methods
 */
  return {
    init: init,
    update: updatePL,
    destroy: destroy,
    isActive: isActive,
    getCurrentTrack: getCurrentTrack,
	getAudio: getAudio,
    changeControls: changeControls,
    lengthPlayList: lengthPlayList,
    playToggle: playToggle,
    next: next,
    close: close
  };

})();

window.AP = AudioPlayer;

})(window);