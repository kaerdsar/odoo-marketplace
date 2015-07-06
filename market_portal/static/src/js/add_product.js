$(document).ready(function() {

    var website = openerp.website;
    var _t = openerp._t;
    
    $('#commodity').on('change', function(){
        var session = new openerp.Session();
        
        session.rpc('/web/dataset/search_read', {
            model: 'market.variety',
            fields: ['name'],
            domain: [['commodity_id', '=', parseInt($('#commodity').val())]]
        }, {}).then(function (result) {
            $('#variety').empty();
            for(var i=0; i < result.records.length; ++i) {
               var option = document.createElement('option');
               option.innerHTML = result.records[i].name;
               option.value = result.records[i].id;
               $('#variety').append(option);
           }
        }, null);
        
        session.rpc('/web/dataset/search_read', {
            model: 'market.package',
            fields: ['name'],
            domain: [['commodity_id', '=', parseInt($('#commodity').val())]]
        }, {}).then(function (result) {
            $('#package').empty();
            for(var i=0; i < result.records.length; ++i) {
               var option = document.createElement('option');
               option.innerHTML = result.records[i].name;
               option.value = result.records[i].id;
               $('#package').append(option);
           }
        }, null);
    });

   
});
