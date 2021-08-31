/**********************************************************************************
* 
*    Copyright (C) 2017 WERP IT GmbH
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('werp_web_utils.snippet_options', function (require) {
"use strict";

var core = require('web.core');
var colorpicker = require('web.colorpicker');
var options = require('web_editor.snippets.options');

var _t = core._t;
var QWeb = core.qweb;

options.registry.colorpicker.include({
	events: _.extend({}, options.registry.colorpicker.prototype.events || {}, {
        'click .mk_add_custom_color': '_onCustomColorButtonClick',
    }),
    start: function () {
        var res = this._super.apply(this, arguments);
        this._renderPickedColors();
        return res;
    },
    onFocus: function () {
        this._renderPickedColors();
    },
    _renderPickedColors: function () {
    	var $editable = window.__EditorMenuBar_$editable;
    	if (this.$el.find('.colorpicker').length && $editable.length) {
    		var $snippets = $editable.find('.mk_custom_background');
    		var colors = _.map($snippets, function ($el) {
                return $el.style.backgroundColor;
            });
            this.$el.find('.colorpicker .mk_custom_color').remove();
            this.$el.find('.colorpicker button.selected').removeClass('selected');
    		_.each( _.uniq(colors), function (color) {
    			var classes = ['mk_custom_color'];
    			if (this.$target.css('background-color') === color) {
    				classes.push('selected');
                }
                var $colorButton = $('<button/>', {
                    style: 'background-color:' + color + ';',
                    class: classes.join(' '),
                });
                this.$el.find('.mk_add_custom_color').before($colorButton);
            }, this);
        }
    },
    _onColorButtonEnter: function (event) {
    	this._super.apply(this, arguments);
    	if ($(event.target).hasClass('mk_custom_color')) {
    		var color = event.currentTarget.style.backgroundColor;
            this.$target.removeClass(this.classes);
            this.$target.css('background-color', color);
            this.$target.trigger('background-color-event', true);
        }
    },
    _onColorButtonClick: function (event) {
    	this._super.apply(this, arguments);
    	var isCustomColor = $(event.target).hasClass('mk_custom_color');
    	this.$target.toggleClass('mk_custom_background', isCustomColor);
        this._renderPickedColors();
    },
    _onCustomColorButtonClick: function () {
        var ColorpickerDialog = new colorpicker(this, {});
        ColorpickerDialog.on('colorpicker:saved', this, function (event) {
        	this.$target.removeClass(this.classes);
        	this.$target.addClass('mk_custom_background');
        	this.$target.css('background-color', event.data.cssColor);
            this.$target.closest('.o_editable').trigger('content_changed');
            this.$target.trigger('background-color-event', false);
            this._renderPickedColors();
        });
        ColorpickerDialog.open();
    },
});

});