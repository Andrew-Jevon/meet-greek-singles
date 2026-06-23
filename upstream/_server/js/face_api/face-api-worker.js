

var urlFaceApi='', faceapi=false,
	_config={inputSize:512, scoreThreshold:0.4},
	_startFaceDetection=0,
	_endFaceDetection=0;

function isFaceDetectionModelLoaded(){
	return !!faceapi.nets.tinyFaceDetector.params
}

async function initFaceDetection(data){
	_startFaceDetection=new Date().getTime();

	if (faceapi === false || !isFaceDetectionModelLoaded()){
		importScripts(
			//"https://cdn.jsdelivr.net/npm/@tensorflow/tfjs",
			//urlFaceApi+'utils/faceEnvWorkerPatch.js',
			urlFaceApi+'face-api.js'

		);

		await faceapi.nets.tinyFaceDetector.load('/');

		postMsgFaceDetection({cmd:'init'});
	}
	_endFaceDetection = new Date().getTime();
	console.log('%cWEB WORKERS initFaceDetection TIME:', 'background:#b1d6fb', (_endFaceDetection - _startFaceDetection)+'ms');

	//checkImageFaceDetection(data, true);
}


var _faceDetectorOptions=false;
function getOptionsFaceDetection(){
	if(_faceDetectorOptions!== false)return _faceDetectorOptions;
	_faceDetectorOptions=new faceapi.TinyFaceDetectorOptions(_config);
	return _faceDetectorOptions;
}

async function checkImageFaceDetection(data, noStart){
	if (!isFaceDetectionModelLoaded())return;
	noStart=noStart||false;
	if (!noStart){
		_startFaceDetection=new Date().getTime();
	}
	var pid=data.pid*1, guid=data.guid,
		options=getOptionsFaceDetection();

	/* Data {bitmap:bitmap, width:w, height:h, pid:0} */

	var w=data.width, h=data.height,
		_canvas = new Canvas(w, h),
		_context = _canvas.getContext('2d');
	_context.drawImage(data.bitmap, 0, 0, w, h);

	var faceDetection = await faceapi.detectAllFaces(_canvas, options)

	_endFaceDetection = new Date().getTime();

	console.log('%cWEB WORKERS checkImageFaceDetection TIME:', 'background:#b1d6fb', (_endFaceDetection - _startFaceDetection)+'ms');

	if (faceDetection) {
		if (faceDetection.length > 1) {
			faceDetection = prepareDataFaceDetection(pid, guid, faceDetection);
		} else {
			faceDetection={};
		}
	} else {
		faceDetection={};
	}

	data = {
		cmd: 'detect_faces',
		pid: pid,
		faces: faceDetection
	}

	postMsgFaceDetection(data);
	console.log('%cWEB WORKERS checkImageFaceDetection RESULT:', 'background:#b1d6fb', faceDetection);
}

function prepareDataFaceDetection(pid, guid, faceDetection){
	var faceDetectionPrepare={};
	if (faceDetection.length > 1) {
		faceDetectionPrepare = {
			image : {
				width : faceDetection[0]._imageDims._width,
				height : faceDetection[0]._imageDims._height,
				photo_id : pid,
				photo_user_id : guid
			},
			face : []
		}
		for (var i in faceDetection) {
			var box=faceDetection[i]._box,
				s=box._width*box._height,
				data={
					left:box.left,
					top:box.top,
					width:box._width,
					height:box._height,
					s:s,
					s1:s
				};
			faceDetectionPrepare['face'][i] = data;
		}
		faceDetectionPrepare['face'].sort(function(a,b){return a.left - b.left;});
	}
	return faceDetectionPrepare;
}

function postMsgFaceDetection(data){
	postMessage({
		type: 'web_worker_data',
		data: data
	});
}

onmessage = function(e) {
	try {
		var data=e.data,
			cmd=data.type, data=data.data;
		console.log('%cWEB WORKERS OnMessage: - ' + cmd, 'background:#5e97ff', e);

		urlFaceApi=data.urlFaceApi;
		switch (cmd) {
			case 'init':
				importScripts(urlFaceApi+'utils/faceEnvWorkerPatch.js');
				if (isBrowserCheck) {
					/*for (let key in data.wnd) {
						if (!self[key]) {
							self[key] = data.wnd[key];
						}
					}
					window = Window = self;*/

					_config=data.config;

					initFaceDetection(data);
				} else {
					console.log('%cWEB WORKERS initFaceDetection:', 'background:red', 'OffscreenCanvas do not support');
					postMsgFaceDetection({cmd:'not_support'});
				}
            break;
			case 'detect_faces':
				checkImageFaceDetection(data);
            break;
		}
	} catch(e) {
		return false;
	}
}

//postMsgFaceDetection({cmd:'init'});