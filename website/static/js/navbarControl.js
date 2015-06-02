
var $ = require('jquery');
var ko = require('knockout');
var bootbox = require('bootbox');
var signIn = require('js/signIn');

/**
    * The NavbarViewModel, for OSF wide navigation.
    * @param {Object} ... 
    */
var NavbarViewModel = function() {
    var self = this;

    self.showSearch = ko.observable(false);
    self.searchCSS = ko.observable('');
    self.query = ko.observable('');
    self.showClose = true;

    self.onSearchPage = ko.computed(function() {
        return window.contextVars.search
    });

    // signIn viewmodel component
    self.signIn = new signIn.ViewModel();

    self.toggleSearch = function(){
        if(self.showSearch()){
            self.showSearch(false);
            self.searchCSS('');
        } else {
            self.showSearch(true);
            self.searchCSS('active');
            $('#searchPageFullBar').focus();
        }
    };

    self.help = function() {
        bootbox.dialog({
            title: 'Search help',
            message: '<h4>Queries</h4>'+
                '<p>Search uses the <a href="http://extensions.xwiki.org/xwiki/bin/view/Extension/Search+Application+Query+Syntax">Lucene search syntax</a>. ' +
                'This gives you many options, but can be very simple as well. ' +
                'Examples of valid searches include:' +
                '<ul><li><a href="/search/?q=repro*">repro*</a></li>' +
                '<li><a href="/search/?q=brian+AND+title%3Amany">brian AND title:many</a></li>' +
                '<li><a href="/search/?q=tags%3A%28psychology%29">tags:(psychology)</a></li></ul>' +
                '</p>'
        });
    };


    self.submit = function() {
        $('#searchPageFullBar').blur().focus();
       if(self.query() !== ''){
           window.location.href = '/search/?q=' + self.query();
       }
    };

};

function NavbarControl (selector, data, options) {
    var self = this;
    self.selector = selector;
    self.$element = $(self.selector);
    self.data = data;
    self.viewModel = new NavbarViewModel(self.data);
    self.options = $.extend({}, {}, options);
    self.init();
}

/** Only for Search Bar Placeholder -- Allow IE and other browsers to work as the same */
function placeholder(inputDom, inputLabel) {
    inputDom.on('input', function () {
        if (inputDom.val() === '') {
            inputLabel.css( "visibility", "visible" );
        } else {
            inputLabel.css( "visibility", "hidden" );
        }
    });
}

function searchBarPlaceHolderInit() {
    var inputDom =  $("#searchPageFullBar");
    var inputLabel =  $("#searchBarLabel");
    inputDom.attr("placeholder", ""); //Clear the original placeholder
    inputLabel.css( "visibility", "visible" );
    placeholder(inputDom, inputLabel);
    inputDom.focus();

    //Make sure IE cursor is located at the end of text
    var $inputVal = inputDom.val();
    inputDom.val('').val($inputVal);

    //For search page with existing input, make sure placeholder is hidden.
    if(inputDom.val() !== '' ){
         inputLabel.css( "visibility", "hidden" );
    }
}

function isIE(userAgent) {
  userAgent = userAgent || navigator.userAgent;
  return userAgent.indexOf("MSIE ") > -1 || userAgent.indexOf("Trident/") > -1;
}


NavbarControl.prototype.init = function() {
    var self = this;
    ko.applyBindings(self.viewModel, self.$element[0]);
    if(isIE()){
        searchBarPlaceHolderInit();
    }
    
};


module.exports = NavbarControl;
