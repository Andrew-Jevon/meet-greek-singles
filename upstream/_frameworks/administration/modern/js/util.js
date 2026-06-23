var MSG_INVALID_DATE_FORMAT = 'Invalid date format.  Must be of the form MM/DD/YYYY.';
var MSG_INVALID_MONTH       = 'Invalid date: %1 month must be in the range 1 - 12';
var MSG_INVALID_DAY         = 'Invalid date: %1 day not valid.';
var MSG_INVALID_YEAR        = 'Invalid date: %1 year must be greater than 1900.';
var MSG_INVALID_EMAIL       = 'Invalid email address: %1';
var MSG_INVALID_DOMAIN      = 'Invalid domain name: %1. The value must be of the form \'mydomain.com\'.';
var MSG_INVALID_PASSWORD    = 'Passwords must be at 6-10 alphanumeric characters!';
var MSG_INVALID_USERID      = 'Usernames may only contain alphanumeric characters and \'_\'!';
var MSG_INVALID_ALPHANUMERIC= 'This field may only contain alphanumeric characters, \'_\' and \'-\'!';
var MSG_INVALID_ALPHANUMERIC_WS= 'This field may only contain alphanumeric characters, \'_\', \'-\' and spaces!';
var MSG_INVALID_URL         = 'URL cannot contain *, " or \'';
var MSG_REQ_FIELD           = '%1 is a required field.';
var MSG_AT_LEAST_ONE_FIELD  = 'At least one of %1 or %2 must be specified.';
var MSG_AT_LEAST_ONE_FIELD_CHANGED  = 'At least one of %1 or %2 must be changed.';
var MSG_MAX_LENGTH			= '%1 may only be a maximum of %2 characters long.';
var MSG_MIN_LENGTH			= '%1 must be a minimum of %2 characters long.';
var MSG_ALPHA_NUMERIC		= '%1 may only contain alphanumeric characters.';
var MSG_ALPHA 				= '%1 may only contain alphabetic characters.';
var MSG_NAME				= '%1 may only contain alphanumeric characters, periods and exclaimation marks.';
var MSG_NUMERIC             = '%1 may only contain numeric characters!';
var MSG_LONG             = '%1 may only contain numeric characters!';
var MSG_TWO_FIELDS			= '%1 and %2 must be the same.';
var MSG_CONFIRM_TWO_FIELDS  = 'Your new password is the same as the old one. Do you want to proceed?';
var MSG_NOT_TWO_FIELDS      = '%1 and %2 may not have the same value.';
var MSG_REQUIRED_SELECT		= 'Please select a value for %1.';
var MSG_FIELD_INVALID       = '%1 is invalid.';
var MSG_TO_AGE_MUST_BIGGER  = 'Please select an Age Range from lowest to highest.';
var MSG_CONFIRM_TRANSACTION = "You are about to process a secure transaction that may take a minute to complete.Please do not click 'Back' on your web browser during the processing,as you will not receive confirmation of your transaction. Do you want to proceed?"
var MSG_INVALID_ZIP_CODE_FORMAT = 'Invalid Zip Code';
var MSG_INVALID_POSTAL_CODE_FORMAT = 'Invalid Postal code';
var MSG_ZIP_5_OR_9='Zip Code must be 5 or 9 numbers.';
var MSG_ZIP_5='Zip Code must be 5 numbers.';
var MSG_TOO_MANY_EMAILS_ADDRESSES='%1 may only contain a maximum of %2 email addresses';
var MSG_PHONE_NUMBER_VALID_CHARACTERS = '%1 may only contain the following the digits 0-9';
var MSG_PHONE_NUMBER_NORTH_AMERICA_INVALID_FORMAT = '%1 must be of the format NXX-NXX-XXXX where N is the digits 2-9 and X is any digit.';
var MSG_PHONE_NUMBER_NORTH_AMERICA_RESERVED_AREA_CODE =  'Reserved area codes, such as 800, 888, 900, etc,  and emergency service numbers, such as 411, 911, etc,  are not permitted.';
var MSG_PHONE_NUMBER_VALID_CHARACTERS = '%1 may only contain the following characters: 0-9()-.';
var MSG_PHONE_NUMBER_NORTH_AMERICA  = '%1 must contain 10 digits.';
var MSG_MOBILE_NUMBER_VALID_CHARACTERS = '%1 may only contain the following the digits 0-9 (Note: The Date Mobile section is optional and can be left blank)';
var MSG_MOBILE_NUMBER_NORTH_AMERICA_INVALID_FORMAT = '%1 must be of the format NXX-NXX-XXXX where N is the digits 2-9 and X is any digit. (Note: The Date Mobile section is optional and can be left blank)';
var MSG_MOBILE_NUMBER_NORTH_AMERICA_RESERVED_AREA_CODE =  'Reserved area codes, such as 800, 888, 900, etc,  and emergency service numbers, such as 411, 911, etc,  are not permitted. (Note: The Date Mobile section is optional and can be left blank)';
var MSG_TOO_MANY_DOMAINS='%1 may only contain a maximum of %2 email addresses';
var MSG_MOBILE_NUMBER_VALID_CHARACTERS = '%1 may only contain the following characters: 0-9()-. (Note: The Date Mobile section is optional and can be left blank)';
var MSG_MOBILE_NUMBER_NORTH_AMERICA  = '%1 must contain 10 digits. (Note: The Date Mobile section is optional and can be left blank)';
var MSG_NUMERIC_MIN          = '%1 must be greater than or equal to %2'
var MSG_NUMERIC_MAX          = '%1 must be less than or equal to %2'
var MSG_MAX_LENGTH_COUNTER	= 'You have reached the maximum of %1 characters for this field.';
var MSG_NON_EMPTY_DEPENDENCY = '%1 has been completed. %2 cannot be empty if %1 has been completed.';
var MSG_SAVED_SEARCH_EMPTY = 'You have selected to save this search but failed to provide a saved search name. Please provide a saved search name.';
var MSG_REGISTRATION_UPLOAD_PHOTO_SKIP_STEP = 'You have filled out the form to upload a photo. Are you sure you want to skip this step?'

/** Validates required field */
function validateRequiredField(field, name, dv)
{
	//Try trim - will fail for input type="file".
	try
	{
		field.value = field.value.trim();
		dv = dv.trim();
	}
	catch(e) {}

	if (field.value.length == 0 || field.value == dv)
	{
		alertCustom(MSG_REQ_FIELD.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Validates that at least one checkbox in the form with the input field name is checked. */
function validateRequiredCheckbox(field, name, msg) {
	if (!isCheckBoxChecked(field)) {
		alertCustom(msg.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Validates required drop down */
function validateRequiredSelect(field, name, defaultValue) {
	if (field.value == null || field.value == '' || field.value == defaultValue) {
		alertCustom(MSG_REQUIRED_SELECT.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	else {
		return true;
	}
}

function validateRequiredMultiSelect(field, name)
{
  var selected = false;
  for (i=0; i<field.length; i++) {
    if (field.options[i].selected) {
      selected = true;
      break;
    }
  }
  if (selected) return true;
	alertCustom(MSG_REQUIRED_SELECT.replace('%1', name));
	try{field.focus();}catch(e){}
	return false;
}

/** Validate that a field is less than or equal to the max length.
	If the value of that field is too large, chop off the extraneous characters. */
function validateMaxLength(field, name, maxLength)
{
	var value = field.value;
	var originalVal = value;	//store a copy with the \n's in it
	var newVal = "";	//new value with any extra characters removed from it so as not to go over maxLength
	var character = null;
	value = value.replace(/\n/g,'**'); // bug #4830 when the javascript validates it sees \n's and java validates it sees \r\n's so a string may pass javascript validation but fail java validation, solution validate on a copy of the string with all \n's replaced with 2 characters to simulate the java length

	if (value.length > maxLength)
	{
		//loop through the string getting one character at a time.
		//If we encounter a \n we have to count it as 2 characters due to bug #4830
		for(var i=0, count=1; count<=maxLength; i++, count++){
				character = originalVal.charAt(i);

				//if this is a new line char make sure we have 2 spaces available in the new string
				if(character == "\n" && count<=maxLength-1){
					newVal = newVal.concat(character);
					count++;
				}else{
					newVal = newVal.concat(character);
				}
		}

		var msg = MSG_MAX_LENGTH.replace('%1', name);
		msg = msg.replace('%2', maxLength);
		alertCustom(msg);
		try{
			//substitute in the shortened string into the field.
			field.value = newVal;
			field.focus();
		}catch(e){}
		return false;
	}
	return true;
}

/** Validate that a field is greater than or equal to the min length. */
function validateMinLength(field, name, minLength) {
	if (field.value.length < minLength) {
		var msg = MSG_MIN_LENGTH.replace('%1', name);
		msg = msg.replace('%2', minLength);
		alertCustom(msg);
		try{field.focus();}catch(e){}
		return false;
	}
	else {
		return true;
	}
}

/** Validates the email field. If the field is not valid, focus is given to that field. */
function validateEmailField(emailField, name)
{
	emailField.value = emailField.value.trim();
	if (isEmpty(emailField)) return true;

	if (!checkEmail(emailField.value)) {
		alertCustom(MSG_INVALID_EMAIL.replace('%1', emailField.value));
		try{emailField.focus();}catch(e){}
		return false;
	}

	return true;
}

/** Validates the email field without checking for bad domains/users etc. */
function validateAnyEmailField(emailField, name)
{
	emailField.value = emailField.value.trim();
	if (isEmpty(emailField)) return true;

	if (!checkAnyEmail(emailField.value)) {
		alertCustom(MSG_INVALID_EMAIL.replace('%1', emailField.value));
		try{emailField.focus();}catch(e){}
		return false;
	}

	return true;
}

/** Validates multiple email fields. If the field is not valid, focus is given to that field. */
function validateMultipleEmailField(field, name, max) {
	field.value = field.value.trim();
	field.value = field.value.replace(/;/g, ',');
	field.value = field.value.replace(/,+/g, ',');
	field.value = field.value.replace(/^,/, '');
	field.value = field.value.replace(/,$/, '');
	//TODO: could check for duplicates...
	var array = field.value.split(",");
	if (array.length > max) {
		alertCustom(MSG_TOO_MANY_EMAILS_ADDRESSES.replace('%1', field.name).replace('%2', max));
		try{field.focus();}catch(e){}
		return false;
	}

	for (var i = 0 ; i < array.length ; i++) {
		array[i] = array[i].trim();
		if (!checkEmail(array[i])) {
			alertCustom(MSG_INVALID_EMAIL.replace('%1', array[i]));
			try{field.focus();}catch(e){}
			return false;
		}
	}
	return true;
}

function validateDomainField(domainField, name){
 domainField.value = domainField.value.trim();
 if (!checkDomain(domainField.value)) {
  alertCustom(MSG_INVALID_DOMAIN.replace('%1', domainField.value));
  try{domainField.focus();}catch(e){}
  return false;
 }
 return true;
}
function validateMultipleDomainField(field, name, max) {
 field.value=field.value.trim();
 field.value=field.value.replace(/;/g, ',');
 field.value=field.value.replace(/,+/g, ',');
 field.value=field.value.replace(/^,/, '');
 field.value=field.value.replace(/,$/, '');
 //TODO: could check for duplicates...
 var array=field.value.split(",");
 if (array.length > max) {
	alertCustom(MSG_TOO_MANY_DOMAINS.replace('%1', field.name).replace('%2', max));
	try{field.focus();}catch(e){}
	return false;
 }
 for (var i=0 ; i < array.length ; i++) {
	array[i]=array[i].trim();
	if (!checkDomain(array[i])) {
	 alertCustom(MSG_INVALID_DOMAIN.replace('%1', array[i]));
	 try{field.focus();}catch(e){}
	 return false;
	}
 }
 return true;
}

/** Checks that a field contains only alphanumeric values */
function validateAlphaNumeric(field, name)
{
	var mask = /^[_0-9a-zA-Z-]*[_0-9a-zA-Z-]$/
	if (!mask.test(field.value)) {
		alertCustom(MSG_ALPHA_NUMERIC.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

function validateAlphaNumeric_search(field, name)
{
	var mask = /^[_0-9a-zA-Z-*]*[_0-9a-zA-Z-*]$/
	if (!mask.test(field.value)) {
		alertCustom(MSG_ALPHA_NUMERIC.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only alphanumeric values */
function validateAlphaNumericWS(field, name)
{
	var mask = /^[_0-9a-zA-Z-\s]*[_0-9a-zA-Z-\s]$/
	if (!mask.test(field.value)) {
		alertCustom(MSG_ALPHA_NUMERIC.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only alphanumeric values and dot*/
function validateAlphaNumericDot(field, name)
{
	var mask = /^[_0-9a-zA-Z-\.]*[_0-9a-zA-Z-\.]$/
	if (!mask.test(field.value)) {
		alertCustom(MSG_ALPHA_NUMERIC.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only numeric values */
function validateNumeric(field, name)
{
	var val = trim(field.value);
	field.value = val;
	var mask = /^-?[0-9]*(\.)?[0-9]*$/
	if (!mask.test(val)) {
		alertCustom(MSG_NUMERIC.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only numeric values */
function validateLong(field, name)
{
	var val = trim(field.value);
	field.value = val;
	if (isEmpty(field)) return true;
	var mask = /^-?[0-9]*[0-9\s]$/
	if (!mask.test(val)) {
		alertCustom(MSG_LONG.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only numeric values and is > a minimum value. */
function validateMinNumeric(field, name, minValue)
{
	if (isEmpty(field)) return true;
	if (!validateNumeric(field, name)) return false;
	var value = trim(field.value);
	if (value < minValue) {
		alertCustom(MSG_NUMERIC_MIN.replace('%1', name).replace('%2', minValue));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only numeric values and is < a maximum value. */
function validateMaxNumeric(field, name, maxValue)
{
	if (isEmpty(field)) return true;
	if (!validateNumeric(field, name)) return false;
	var value = trim(field.value);
	if (value > maxValue) {
		alertCustom(MSG_NUMERIC_MAX.replace('%1', name).replace('%2', maxValue));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only numeric values */
function validateNumericWS(field, name)
{
	var val = trim(field.value);
	if (val == null || val == '') return true;
	var mask = /^[0-9-\s]*[0-9-\s]$/
	if (!mask.test(val)) {
		alertCustom(MSG_NUMERIC.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains only alphanumeric values */
function validateAlpha(field, name)
{
	var mask = /^[_a-zA-Z-\s~]*[_a-zA-Z-\s~]$/
	if (!mask.test(field.value)) {
		alertCustom(MSG_ALPHA.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Checks that a field contains alphanumeric values, periods and exclamation marks only */
function validateName(field, name)
{
	var mask = /^[_a-zA-Z-\s~\.!']*[_a-zA-Z-\s~\.!']$/
	if (!mask.test(field.value)) {
		alertCustom(MSG_NAME.replace('%1', name));
		try{field.focus();}catch(e){}
		return false;
	}
	return true;

}

/** Validates the first field is greater than or equal to the second field*/
function confirmNoLess(field,name,field2,name2)
{
	if (Number(field.value) < Number(field2.value)){
		var msg = MSG_TO_AGE_MUST_BIGGER.replace('%1',name);
		msg = msg.replace('%2',name2);
		alertCustom(msg);
		field.focus();
		return false;
	}else{
		return true
	}
}

/** Validates that two fields have the same value and ask for confirmation*/
function confirmTwoFields(field,name,field2,name2)
{
	if (field.value == field2.value)
	{
		var msg = MSG_CONFIRM_TWO_FIELDS;
		field.focus();
		return confirm(msg);
	}else
	{
		return true
	}

}

/** Validates that at least one of the specified fields is present. Displays default message. */
function validateAtLeastOneField(field,name,field2,name2) {
  var msg = MSG_AT_LEAST_ONE_FIELD.replace('%1', name);
  msg = msg.replace('%2', name2);
	return validateAtLeastOneField(field,name,field2,name2,msg);
}

/** Validates that at least one of the specified fields is present */
function validateAtLeastOneField(field,name,field2,name2,msg) {
	if (isEmpty(field)&&isEmpty(field2))
	{
		alertCustom(msg);
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Validates that two fields have the same value */
function validateTwoFields(field,name,field2,name2) {
	if (field.value != field2.value){
		var msg = MSG_TWO_FIELDS.replace('%1', name);
		msg = msg.replace('%2', name2);
		alertCustom(msg);
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Validates that two fields have the same value, disregarding case */
function validateTwoFieldsIgnoreCase(field,name,field2,name2) {
	if (field.value.toLowerCase() != field2.value.toLowerCase()){
		var msg = MSG_TWO_FIELDS.replace('%1', name);
		msg = msg.replace('%2', name2);
		alertCustom(msg);
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Validates that two fields do not have the same value */
function validateNotTwoFields(field,name,field2,name2) {
	if (field.value == field2.value){
		var msg = MSG_NOT_TWO_FIELDS.replace('%1', name);
		msg = msg.replace('%2', name2);
		alertCustom(msg);
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/**
 * This checks to make sure that field1 is non-empty. If it is non-empty then
 * field2 must be non-empty. If field1 is empty then we don't care
 * if field2 is empty or not. Basically, a check of field2 is only
 * dependent on field1 being empty or not.
 */
function nonEmptyDependency(field1, field1Name, field2, field2Name, message){
	if(!isEmpty(field1) && isEmpty(field2)){
		alertCustom(message);
		return false;
	}else{
		return true;
	}
}

/**
 * Reference: Sandeep V. Tamhankar (stamhankar@hotmail.com),
 * http://javascript.internet.com
 */
function checkEmail(emailStr) {
	var emailPat=/^(.+)@(.+)$/;
	var specialChars="\\(\\)><@,;:\\\\\\\"\\.\\[\\]!%";
	var validChars="\[^\\s" + specialChars + "\]";
	var quotedUser="(\"[^\"]*\")";
	var ipDomainPat=/^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$/;
	var atom=validChars + '+';
	var word="(" + atom + "|" + quotedUser + ")";
	var userPat=new RegExp("^" + word + "(\\." + word + ")*$");
	var domainPat=new RegExp("^" + atom + "(\\." + atom +")*$");

	var matchArray=emailStr.match(emailPat);

	if (matchArray==null) {
		return false;
	}
	var user=matchArray[1];
	var domain=matchArray[2];

	for (i=0; i<user.length; i++) {
		if (user.charCodeAt(i)>127) {
			return false;
		}
	}
	for (i=0; i<domain.length; i++) {
		if (domain.charCodeAt(i)>127) {
			return false;
		}
	}

	if (user.match(userPat)==null) {
		return false;
	}

	var IPArray=domain.match(ipDomainPat);
	if (IPArray!=null) {
		for (var i=1;i<=4;i++) {
			if (IPArray[i]>255) {
				return false;
			}
		}
		return true;
	}

	var atomPat=new RegExp("^" + atom + "$");
	var domArr=domain.split(".");
	var len=domArr.length;
	for (i=0;i<len;i++) {
		if (domArr[i].search(atomPat)==-1) {
			return false;
		}
	}

	if (domArr[len-1].length < 2) {
		return false;
	}

	if (len<2) {
		return false;
	}

	var mask=/@(date.com|date.net|matchmaker.com|matchmaker.net|matchmaker.org|matchmaker.biz|mm.org|gay.com|wellsfargo.com|spamhole.com|mailinator.com|klassmaster.com|fakeinformation.com|sogetthis.com|spambob.com|spamgourmet.com|spamex.com)/i;
	if (mask.test(emailStr.toLowerCase())) {
		return false;
	}
	/*mask=/^(root|abuse|webmaster|help|postmaster|sales|resumes|contact|advertising|spam|spamtrap|nospam|noc|admin|support|daemon|listserve|listserver|autoreply)@/i;
	if (mask.test(emailStr.toLowerCase())) {
		return false;
	}*/

	return true;
}

/**
 * Reference: Sandeep V. Tamhankar (stamhankar@hotmail.com),
 * http://javascript.internet.com
 */
function checkAnyEmail(emailStr) {
	var emailPat=/^(.+)@(.+)$/;
	var specialChars="\\(\\)><@,;:\\\\\\\"\\.\\[\\]!%";
	var validChars="\[^\\s" + specialChars + "\]";
	var quotedUser="(\"[^\"]*\")";
	var ipDomainPat=/^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$/;
	var atom=validChars + '+';
	var word="(" + atom + "|" + quotedUser + ")";
	var userPat=new RegExp("^" + word + "(\\." + word + ")*$");
	var domainPat=new RegExp("^" + atom + "(\\." + atom +")*$");

	var matchArray=emailStr.match(emailPat);

	if (matchArray==null) {
		return false;
	}
	var user=matchArray[1];
	var domain=matchArray[2];

	for (i=0; i<user.length; i++) {
		if (user.charCodeAt(i)>127) {
			return false;
		}
	}
	for (i=0; i<domain.length; i++) {
		if (domain.charCodeAt(i)>127) {
			return false;
		}
	}

	if (user.match(userPat)==null) {
		return false;
	}

	var IPArray=domain.match(ipDomainPat);
	if (IPArray!=null) {
		for (var i=1;i<=4;i++) {
			if (IPArray[i]>255) {
				return false;
			}
		}
		return true;
	}

	var atomPat=new RegExp("^" + atom + "$");
	var domArr=domain.split(".");
	var len=domArr.length;
	for (i=0;i<len;i++) {
		if (domArr[i].search(atomPat)==-1) {
			return false;
		}
	}

	if (domArr[len-1].length < 2) {
		return false;
	}

	if (len<2) {
		return false;
	}

	return true;
}

function checkDomain(domain) {
    if (/^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/.test(domain)) {
        return true;
    }
    return false;


	var specialChars="\\(\\)><@,;:\\\\\\\"\\.\\[\\]!%";
	var validChars="\[^\\s" + specialChars + "\]";
	var ipDomainPat=/^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$/;
	var atom=validChars + '+';
	var domainPat=new RegExp("^" + atom + "(\\." + atom +")*$");

	for (i=0; i<domain.length; i++) {
		if (domain.charCodeAt(i)>127) {
			return false;
	   }
	}

	var IPArray=domain.match(ipDomainPat);
	if (IPArray!=null) {
		for (var i=1;i<=4;i++) {
			if (IPArray[i]>255) {
				return false;
			}
		}
		return true;
	}

	var atomPat=new RegExp("^" + atom + "$");
	var domArr=domain.split(".");
	var len=domArr.length;
	for (i=0;i<len;i++) {
		if (domArr[i].search(atomPat)==-1) {
			return false;
		}
	}

	if (domArr[len-1].length < 2) {
		return false;
	}

	if (len!=2) {
		return false;
	}

	var mask=/date.com/i;
	if (mask.test(domain.toLowerCase())) {
		return false;
	}
	mask=/date.net/i;
	if (mask.test(domain.toLowerCase())) {
		return false;
	}
	mask=/date.info/i;
	if (mask.test(domain.toLowerCase())) {
		return false;
	}

	return true;
}

/** Validates a URL. */
function validateURL(field)
{
	var str = field.value;
	if ( str.indexOf("*") != -1 || str.indexOf('"') != -1 || str.indexOf("'") != -1 ) {
		alertCustom(MSG_INVALID_URL);
		try{field.focus();}catch(e){}
		return false;
	}
	return true;
}

/** Returns true if the string only contains digits. */
function validateNumber(str, scale, precision)
{
	if (precision == 0) {
		var format = new RegExp('^\\s*\\d{0,'+scale+'}\\s*$');
		return format.test(str);
	}
	var format = new RegExp('^\\s*\\d{0,'+(scale-precision)+'}\\.\\d{0,'+precision+'}\\s*$');
	if ( format.test(str) ) {
		return true;
  	} else {
		format = new RegExp('^\\s*\\d{0,'+scale+'}\\s*$');
		return format.test(str);
  	}
}

/** THE FOLLOWING ARE NOT CURRENTLY IN USE **/
/** Validates a date string returns true if it is of the form MM/DD/YYYY. */
function validateDate(str)
{
  // Validate format
  var dateformat = /^\s*\d{1,2}\/\d{1,2}\/\d{2,4}\s*$/;  // MM/DD/YYYY

  if ( !dateformat.test(str) ) {
	alertCustom(MSG_INVALID_DATE_FORMAT);
	return false;
  }

  var elements = str.split('/');

  // check month
  var month = elements[0];
  if (month < 1 || month > 12) {
	alertCustom(MSG_INVALID_MONTH.replace('%1', str));
	return false;
  }

  // check day
  var day = elements[1];
  if (!validDate(month, day)) {
	alertCustom(MSG_INVALID_DAY.replace('%1', str));
	return false;
  }

  // check year
  var year = elements[2];
  if (year < 100 && year > 50) year += 1900;
  else if (year > 0 && year < 50) year += 2000;

  if (year < 1900) {
	alertCustomCustom(MSG_INVALID_YEAR.replace('%1', str));
	return false;
  }


  return true;
}

/** Checks to make sure the number of days in the month is correct.  This does
	not work in all cases (ie February) */
function validDate(month, value)
{
  var monthMax = new Array (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31) ;
  month = month - 1;

  var top = monthMax[month];
  if (value > top) return false; // value is greater than highest for the month
  else return true;
}