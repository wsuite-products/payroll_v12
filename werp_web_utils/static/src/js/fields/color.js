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

odoo.define('werp_web_utils.ColorChar', function (require) {
"use strict";

var core = require('web.core');
var fields = require('web.basic_fields');
var registry = require('web.field_registry');
var colorpicker = require('web.colorpicker');

var _t = core._t;
var QWeb = core.qweb;

var FieldColor = fields.InputField.extend({
	events: _.extend({}, fields.InputField.prototype.events, {
		"click .mk_field_color_button": "_onCustomColorButtonClick",
    }),
    template: "werp_web_utils.FieldColor",
    supportedFieldTypes: ['char'],
    start: function() {
    	this.$input = this.$('.mk_field_color_input');
    	return this._super.apply(this, arguments);
    },
    _renderEdit: function () {
        this.$('.mk_field_color_input').val(
        	this._formatValue(this.value)
        );
        this.$('.mk_field_color_input').css({
        	'background-color': this._formatValue(this.value),
        });
    },
    _renderReadonly: function () {
        this.$el.text(this._formatValue(this.value));
        this.$el.css({'color': this._formatValue(this.value)});
    },
    _doAction: function() {
    	this._super.apply(this, arguments);
    	this.$('.mk_field_color_input').css({
        	'background-color': this._getValue(),
        });
    },
    _formatValue: function (value) {
    	return value;
    },
    _parseValue: function (value) {
    	if((/(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i).test(value)) {
    		return value;
    	} else {
    		throw new Error(_.str.sprintf(core._t("'%s' is not a correct color value"), value));
    	}
    },
    _onCustomColorButtonClick: function () {
        var ColorpickerDialog = new colorpicker(this, {
        	dialogClass: 'mk_field_color_picker',
        	defaultColor: this._getValue(),
        });
        ColorpickerDialog.on('colorpicker:saved', this, function (event) {
        	this.$input.val(event.data.hex);
        	this._doAction();
        });
        ColorpickerDialog.open();
    },
});

registry.add('color', FieldColor);

return FieldColor;

});