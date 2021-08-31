// Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
if (sessionStorage.getItem("switchdatabaseurl")) {
    setTimeout(function () {
        window.location.href=sessionStorage.getItem("switchdatabaseurl");
        sessionStorage.removeItem("switchdatabaseurl");
    }, 1000);
}

$(function() {
    if(localStorage['username'] && localStorage['password']) {
        $(".container").css("visibility", "hidden");
        $("body").append("<div style='padding: 0% 37%;'><img style='top: 40%; position: fixed; margin-left: 8%;' src='/base_switch_database/static/src/img/loading.gif' /></div>");
        $(".bg-100").attr('style', 'background-color: #ffffff !important');
        $('.oe_login_form input[name="login"]').val(localStorage['username']);
        $('.oe_login_form input[name="password"]').val(localStorage['password']);
        setTimeout(function(){
            $('.oe_login_form').trigger('submit');
        }, 1000);
        delete localStorage['password'];
        delete localStorage['username'];
    }
})
