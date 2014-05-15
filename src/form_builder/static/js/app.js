(function() {

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  _.templateSettings = {
    interpolate : /\{\{(.+?)\}\}/g,
    evalulate: /\{%(.+?)%\}/g
  };

  var formsetNum = $("#id_field_set-TOTAL_FORMS").val();

  var updateFormsetNum = function () {
    formsetNum++;
    $("#id_field_set-TOTAL_FORMS").val(formsetNum);
    return formsetNum;
  };

  var render = function (template, attrs) {
    return _.template(template)(attrs);
  };

  var optionize = function(el) {
    var $el = $(el);
    var tmpl = $('#field-option-add').html();
    $el.find('.choices').parents('.control-group').after(render(tmpl));
  };

  $(function(){

    var csrftoken = getCookie('csrftoken');

    var makeForm = function (url) {
      return $("<form action='" + url + "' method='POST'>" +
               "<input type='hidden' name='csrfmiddlewaretoken' value='" +
               csrftoken + "' /></form>");
    };

    // sticky edit sidebar
    var sticky = $('.admin-tools > div');
    if (sticky.length > 0) {
      sticky.affix({offset: sticky.offset().top});
    }


    // datepicker
    $('input#id_end_date').datepicker({
      minDate: 0
    });
      // .next('.btn-datepicker')
      // .click(function (event) {
      //   event.preventDefault();
      //   $('input.end-date').focus();
      // });

    // tooltips on manage forms page
    $('.manage .controls a').tooltip({
      placement: 'bottom'
    });

    // show controls on manage forms page
    $('.manage tbody tr').on({
      click: function() {
        window.location = $(this).find('.title').attr('href');
      },
      mouseover: function() {
        $(this).find('.invis').show();
      },
      mouseleave: function() {
        $(this).find('.invis').hide();
      }
    });

    // prevent bubbling up to tr element
    $('.manage tr a').on('click', function(e) {
        e.stopPropagation();
    });

    $('.manage .inactive').on('click', function (e) { e.preventDefault(); });

    $('.manage .delete').on('click', function (e) {
      e.preventDefault();
      makeForm($(this).attr('href')).appendTo("body").submit();
    });

    $('.manage .duplicate').on('click', function (e) {
      e.preventDefault();
      makeForm($(this).attr('href')).appendTo("body").submit();
    });

    // share form modal
    $('.share').on('click', function(e){
      e.preventDefault();
      $('#share').modal('show');
      var url = window.location.protocol + "//" + window.location.host + $(this).attr('href');
      $('#share').find('input').val(url).select();
      $('.modal-backdrop').appendTo('#form-builder');
    });

    // share link popover
    /*$('#share').on('shown', function() {
      $(this).popover('show');
    });

    $('#share').on('hidden', function() {
      $(this).popover('hide');
    });*/

    // form manager
    $('.save-form-button').click(function () {
        $('.field').each (function () {
            var choices = $.makeArray(
              $(this).find('.edit-option input').map(function () {
                return $(this).val();
              })
            ).join(";").replace(/\;$/, '');

            $(this).find('.choices').val(choices);
        });

        /*
        Iterate through the questions to determine their order on the form.
        Used when re-ordering fields during the edit process.
        */
        var fieldOrder = $('.field').map(function(){
            if (!$(this).find("input[id$=-DELETE]").prop('checked')) {
              return $(this).find("input[id$=-id]").val();
            }
        }).get().join(',');

        $('#field_order').val(fieldOrder);

        $("#form-form").submit();
    });

    $('.preview-form-button').click(function () {
      $('.save-form-button').click();
      window.open("/forms/respond/" + $("#form-form").attr("action").replace("/forms/edit/", ""));
    });

    /*
    FORM AUTOSAVE
    =============
    When the form is submitted, save form data and make necessary changes to DOM
    to return it to the state it would be in if we came to the edit screen for the
    first time. This means removing deleted fields and reordering formsets, primarily.

    NOTE: If adding functionality that saves the form, call:

      $('.save-form-button').click();

    and not:

      $("#form-form").submit();

    The latter would prevent some necessary code from executing, particularly ensuring
    that multiple choice question options are saved properly.
    */
    if (window.use_form_autosave === 1) {
    $("#form-form[action^='/forms/edit']").submit(function() {

      $.ajax({
        data: $(this).serialize(), // get the form data
        type: $(this).attr('method'), // GET or POST
        url: $(this).attr('action'), // the file to call
        success: function(response) { // on success...
          var checkDict = {};
          var fCount = 0;
          if (!(jQuery.isEmptyObject(response.formfields)) && ($('input[id$=-DELETE]:checked').length>0)) {
            $('input[id$=-DELETE]:checked').closest('li').remove(); // remove deleted questions
          }
          $('.field').each(function(){
            /*
            Create a dictionary of fields currently on the form in the order they appear.
            Change the field_set values to match the order and number of fields on the form
            since these may have been altered between when the form was first drawn and
            the last save.
            */
            checkDict[$(this).find("input[id$=-id]").val()] = $(this).find("input[id$=-label]").val();

            $(this).find("[id*='field_set-']").each(function(){
              $(this).attr('id',$(this).attr('id').replace(/[0-9]+/g, fCount));
            });
            $(this).find("[name*='field_set-']").each(function(){
              $(this).attr('name',$(this).attr('name').replace(/[0-9]+/g, fCount));
            });
            $(this).find("[for*='field_set-']").each(function(){
              $(this).attr('for',$(this).attr('for').replace(/[0-9]+/g, fCount));
            });
            fCount++;
          });
          var countFields = 0;
          $.each(response.formfields, function(key, value){
            /*
            Search through the dictionary of fields for ones that were added by the last
            save. Insert the field_id for those new fields so that the fields can be sortable
            and so that they will be handled properly by the next save (i.e.: not added to the
            database a second time).
            */
            countFields++;
            if (!(key in checkDict)) {
              var fieldNum;
              $('.field').each(function(){
                if ($(this).find("input[id$=-label]").val() === value) {
                  fieldNum = $(this).find("input[id$=-label]").attr('id').match(/[0-9]+/g);
                  $(this).find("input[name='csrfmiddlewaretoken']").before('<input type="hidden" name="field_set-' + fieldNum + '-id" id="id_field_set-' + fieldNum + '-id" value="' + key + '">');
                  $(this).find(".field-controls").before('<div class="draggable" align="center" title="" data-original-title="You can drag and drop your questions to change the order they will appear in your form."><i class="icon-reorder"></i></div>');
                  $(this).closest("li").attr("class", "field");
                  $(this).attr("class", "");
                }
              });
            }
          });
          // reset the formset counts
          if (!(jQuery.isEmptyObject(response.formfields))) {
            $("#id_field_set-INITIAL_FORMS").val(countFields);
            $("#id_field_set-TOTAL_FORMS").val(countFields);
            formsetNum = countFields;
          }
          // display success message to user
          $("#messages").hide(200)
                        .delay(200)
                        .queue(function(n) {
                          $(this).html(response.message);
                          $(this).addClass('alert');
                          n();
                        })
                        .show(200);
        },
        error: function(response) {
          // display error message if something went wrong
          window.alert("There was an error: " + response);
        }
      });
      return false;
    });
    }

    // add new field
    $('.add-field').on('click', function() {
      var fieldType = $(this).attr('data-field-type'),
          template = $("#template-" + fieldType).html(),
          num;

      updateFormsetNum();
      num = formsetNum - 1;
      $('#fields ul').append(render(template, {i: num}));

      $('.add-first-prompt').hide();
      $('#content > .messages').hide();

      $('.field .choices').parents('.control-group').hide();

      optionize('.field-num-' + num);
    });

    // optionize on page load for fields that were already in the form
    $('fieldset input.choices').each(function(){
      var options = $(this).val().split(';'),
          container = $(this).parents('.control-group');

      container.hide();
      var tmpl = $('#field-option-add').html();
      container.after(render(tmpl));

      tmpl = $('#field-option-remove').html();
      var optionsStr = "";

      $.each(options, function(index, value) {
          optionsStr += _.template(tmpl, {label: value});
//        container.after(_.template(tmpl, {label: value}));
      });
      container.after(optionsStr);
    });

    // delete field
    $(document).on('click', '.field-controls .delete', function() {
      $(this).parents('.field').fadeOut(100).find('.delete-field input').prop('checked', true);
      $(this).parents('.field');
    });

    // add new option field
    $(document).on('click', '.add-option', function(e){
      e.preventDefault();
      var label = $(this).siblings('input').val();
      if (label && label.length > 0) {
        var template = $('#field-option-remove').html();
        $(this).parents('.edit-option').before(_.template(template, {label: label}));
        $(this).siblings('input').val('').select();
      }
    });

    // remove option
    $(document).on('click', '.remove-option', function(e){
      e.preventDefault();
      $(this).parents('.edit-option').hide(100, function(){
        $(this).remove();
      });
    });

    // jquery sortable
    $('.fields ul').sortable({
      placeholder: 'sort-fields-placeholder',
      cursor: 'move',
      handle: '.draggable',
      cancel: '.not-draggable', //cannot position new fields until they have been saved
      start: function(event, ui) {
        var h = $(ui.item).height();
        $('.sort-fields-placeholder').css('height', h + 'px');
      }
    });

  });

})();
