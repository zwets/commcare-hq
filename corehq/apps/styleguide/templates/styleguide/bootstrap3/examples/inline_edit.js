$(function () {
  var inlineEditExample = function () {
    var self = {};

    self.text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.';

    // This should be a real url, either hard-coded in the django template or registered with the
    // registerurl template tag and then feteched here using initial_page_data.js's reverse.
    self.url = '';

    return self;
  };

  $("#inline-edit-example").koApplyBindings(inlineEditExample());
});
