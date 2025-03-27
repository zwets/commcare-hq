let listener = function() {
  console.log("Triggered willSelectAllListener");
};

$(function () {
  var multiselect_utils = hqImport('hqwebapp/js/multiselect_utils');
  multiselect_utils.createFullMultiselectWidget('example-multiselect', {
    selectableHeaderTitle: gettext("Available Letters"),
    selectedHeaderTitle: gettext("Letters Selected"),
    searchItemTitle: gettext("Search Letters..."),
    disableModifyAllActions: false,
    willSelectAllListener: listener,
  });
});
