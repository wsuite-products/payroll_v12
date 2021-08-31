// Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
odoo.define('base_switch_database.ServerUser', function(require) {
"use strict";

    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var dataManager = require('web.data_manager');
    var ajax = require('web.ajax');
    var _t = core._t;

    var ServerUser = Widget.extend({
        template: 'ServerUser',
        events: {
            'click .dropdown-item[data-menu]': '_onClick',
        },
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            this._onClick = _.debounce(this._onClick, 1500, true);
        },
        /**
         * @override
         */
        start: function () {
            var self = this;
            var user_server_list = '';
            $('.o_server_user_menu').addClass('o_hidden');
            self._rpc({
                model: 'res.users.servers',
                method: 'search_read',
                args: [[["user_id", "=", session.uid]], ['id', 'server_id', 'company_id', 'switch_database_url', 'is_microsoft_login', 'is_w_admin']],
            }).then(function (user_servers) {
                if (user_servers.length > 0) {
                    $('.o_server_user_menu').removeClass('o_hidden');
                }
                _.each(user_servers, function (user_server) {
                var avatar_src = session.url('/web/image', {
                    model:'res.users.servers',
                    field: 'image_company',
                    id: user_server.id,
                });
                user_server_list += '<a href="#" server_id="'+ user_server.server_id[0] + '" is_microsoft_login=" '+user_server.is_microsoft_login+'" is_w_admin=" '+ user_server.is_w_admin + '" class="dropdown-item" data-menu="user_server" switch_database_url="' +
                                user_server.switch_database_url + '"><img height="25" width="25" src=" '+
                                avatar_src+'" alt="Avatar" class="rounded-circle oe_topbar_avatar"/><span style="margin-left:1.25em;" class="oe_topbar_name">' +
                                user_server.company_id[1] + '</span></a>';
                });
            self.$('.dropdown-menu').html(user_server_list);
            });
            return self._super();
        },
        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onClick: function (ev) {
            var self = this;
            var UserSyncServerId = $(ev.currentTarget).attr('server_id');
            var UserServer = $(ev.currentTarget).attr('switch_database_url');
            var MicrosoftAccount = $(ev.currentTarget).attr('is_microsoft_login');
            var wadmin = $(ev.currentTarget).attr('is_w_admin');
            if (MicrosoftAccount.includes("true")) {
                ajax.jsonRpc('/microsoftlogin', 'call', {'url_database': UserServer, 'provider': 'Log in with Microsoft'})
                    .then(function (result) {
                        window.location.href = UserServer;
                        window.open(result);
                    });
            }
            else if (wadmin.includes("true")) {
                ajax.jsonRpc('/microsoftlogin', 'call', {'url_database': UserServer, 'provider': 'Log in with W-Suite'})
                    .then(function (result) {
                        window.location.href = UserServer;
                        window.open(result);
                    });
            }
            else {
                self._rpc({
                    model: 'base.synchro.server',
                    method: "search_read",
                    fields: ['login', 'password', 'server_db'],
                    domain: [['id', '=', parseInt(UserSyncServerId)]],
                    }).then(function (values) {
                        var username = values[0]['login'];
                        var password = values[0]['password'];
                        var db = values[0]['server_db'];
                        localStorage['username'] = username;
                        localStorage['password'] = password;
                        setTimeout(function(){
                            window.location.href = "/web?db="+db;
                        }, 1000);
                });
//                sessionStorage.setItem("switchdatabaseurl", UserServer);
//                window.open(UserServer, "_self");
//                window.open('/web/autologin?&id='+UserSyncServerId, "_self")
            }
        },
    });
    SystrayMenu.Items.push(ServerUser);
    return ServerUser;
});
