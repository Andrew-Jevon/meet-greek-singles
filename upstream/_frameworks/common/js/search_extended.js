function extendedSearchInit(extendedSearchActiveClass) {

    var extendedSearchActiveClass = extendedSearchActiveClass || 'active';

    isFilterOnchangeActive = true;
    moduleFilterActiveFields = {};

    $('#link_filter_extended').click(function(){
        console.log('#link_filter_extended click');
        if(!userAllowedFeature['extended_search']){
            window.location.href = urlPageUpgrade;
            return false;
        }
        $('.filter_extended').slideToggle(200);
        return false;
    });

    $('#filter_module_1, #filter_module_2, #filter_module_3').change(function(){
        var filterModule = $(this).attr('id');
        var filterModuleClass = filterModule + '_field';
        var filterModuleField = '.' + filterModuleClass;

        $(filterModuleField + ' .fieldItem').prop('disabled', 'disabled');
        $(filterModuleField).appendTo('.filter_fields_set');
        $(filterModuleField).removeClass(filterModuleClass);

        var filterField = $(this).val();
        //console.log('show', '#filter_field_p_' + filterField);

        var filterFieldPrevValue = '';
        if(filterModule in moduleFilterActiveFields) {
            filterFieldPrevValue = moduleFilterActiveFields[filterModule];
        }

        //console.log('filter field value', typeof filterField, filterField);

        var filterIndex;

        for(filterIndex = 1; filterIndex <= 3; filterIndex++) {
            if('filter_module_' + filterIndex != filterModule) {
                if(filterField !== '0') {
                    fieldOptionDisable('#filter_module_' + filterIndex, filterField);
                }
                if(filterFieldPrevValue) {
                    fieldOptionEnable('#filter_module_' + filterIndex, filterFieldPrevValue);
                }
            }
        }

        if(filterField) {
            console.log('filterField move to main hidden list', filterField);
            $('#filter_field_p_' + filterField + ' .fieldItem, ' + '#filter_field_p_' + filterField + '_from .fieldItem')
            .prop('disabled', '');
            $('#filter_field_p_' + filterField + ', ' + '#filter_field_p_' + filterField + '_from').addClass(filterModuleClass).appendTo($('.' + filterModule).parent());
            console.log('add field');
        }

        setLabelExtendedSearch();
        // active value in current filter
        moduleFilterActiveFields[filterModule] = filterField;
    });

    function fieldOptionDisable(selector, values)
    {
        fieldChangeOptionDisabledStatus(selector, values, 'disabled');
    }

    function fieldOptionEnable(selector, values)
    {
        fieldChangeOptionDisabledStatus(selector, values, '');
    }

    function fieldChangeOptionDisabledStatus(selector, values, status)
    {
        $(selector + ' option').each(function() {
            var option = $(this);
            if(typeof values !== 'object') {
                //console.log('not array');
                valuesKey = values;
                values = [];
                values[valuesKey] = true;
            }

            var isDisabled = false;
            for(key in values) {
                //console.log(key, values[key]);
                if(option.val() == key) {
                    option.prop('disabled', status);
                    isDisabled = true;
                }
            }
        })
    }

    function setLabelExtendedSearch(isActive)
    {
        var isActive = isActive || false;
        var $extendedSearchHref = $('#link_filter_extended');

        if(!isActive) {

            var params = $('.filter_field')
                        .find('input[name],select[name],textarea[name]')
                        .not('.field_filter_disabled').map(function () {
                            return $(this).val().trim() == '' ? null : this;
                        }).serialize();
            //console.log('setLabelExtendedSearch', params);
            if (params !== '') {
                isActive = true;
            }

        }

        if(isActive) {
            $extendedSearchHref.addClass(extendedSearchActiveClass);
        } else {
            $extendedSearchHref.removeClass(extendedSearchActiveClass);
        }

    }

    $('.filter_extended').change(function(e){
        if(!isFilterOnchangeActive) {
            return;
        }
        var el = $(e.target);
        if (el.data('checkbox')) {
            var type = el.data('checkbox'),
                id = el.attr('id'),
                val = el.val();
            if (val != 0) {
                $('[id != "'+id+'"][data-checkbox='+type+']').each(function(){
                    if ($(this).val() === val) {
                        showAlert(l('you_have_already_chosen_this_option'), '.st-container');
                        el.val(lastValueCheckbox);
                        return false;
                    }
                })
            } else {
                var countSelect = $('[data-checkbox='+type+']').length;
                if (countSelect > 1) {
                    var filterModule = el.closest('.filter_extended_select');
                    filterModule.find('select').removeClass('lastSelect');
                    el.parent().remove();
                    var elementIdNumber = parseInt(id.replace('chk_' + type + '_', ''));
                    var fieldIdBaseList = ['field_checkbox_' + type + '_', 'chk_' + type + '_'];
                    for(var fieldNumber = elementIdNumber; fieldNumber <= countSelect; fieldNumber++) {
                        for(var fieldIdBaseListIndex in fieldIdBaseList) {
                            var fieldIdBase = fieldIdBaseList[fieldIdBaseListIndex];
                            var fieldIdOld = fieldIdBase + (fieldNumber + 1);
                            var fieldIdNew = fieldIdBase + fieldNumber;
                            $('#' + fieldIdOld).attr({id: fieldIdNew});
                            console.log('fieldIdNew', fieldIdNew, fieldIdOld);
                        }
                    }
                }
                $('#link_add_'+type).show();
            }
        }
        setLabelExtendedSearch();
    });

    $('.filter_field .link_add').click(function(){
        console.log('link add click');
        var el = $(this),
            type = el.data('typeAdd'),
            previousFieldBlock = el.closest('.field_checkbox_value'),
            baseFieldBlock = $('#field_checkbox_' + type + '_0'),
            baseSelect = $('#chk_' + type + '_0'),
            countOptions = baseSelect.find('option').length,
            countSelects = $('[data-checkbox=' + type + ']').length,
            lastSelect = false;

        if (countOptions <= (countSelects + 2)) {
            el.hide();
            lastSelect = true;
        }
        if (countOptions > (countSelects + 1)) {
            var newFieldSuffix = '_' + type + '_' + countSelects;
            var newSelect = baseSelect.clone(false).attr({id: 'chk' + newFieldSuffix});

            if(lastSelect) {
                newSelect.addClass('lastSelect');
            }

            var newFieldBlock = baseFieldBlock.clone(false).attr({id: 'field_checkbox' + newFieldSuffix}).html('').append(newSelect);
            newFieldBlock.find('option').removeAttr('selected').eq(0).attr({selected: 'selected'}).end().end().find('select');
            newFieldBlock.insertBefore(el);
        }

        console.log('.filter_field .link_add click', countOptions, countSelects, lastSelect);

        return false;
    });

    var lastValueCheckbox;
    $('body').on('click', 'select[data-checkbox]', function(e){
        lastValueCheckbox=$(this).val();
    })
}
