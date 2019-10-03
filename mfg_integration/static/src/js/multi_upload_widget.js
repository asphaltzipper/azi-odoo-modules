odoo.define('mfg_integration', function(require)
{
    'use strict';
    var core = require('web.core');
    var Char = core.form_widget_registry.get('char');

    var import_files_button = Char.extend({
       template : "import_files_button",
        events : {
           'change' : 'import_files',
        },
        init : function(){
           this._super.apply(this,arguments);
           this._start = null;
        },
        start : function() {
        },
        import_files : function(event){
            var self = this;
            var files = event.target.files;
            var attachment_ids = self.getParent().fields[ 'drg_file_ids' ];
            var data64 = null;
            var values_list = [];
            _.each(files, function(file){
                if(self.already_attached(attachment_ids.get_value(),file.name)){
                    return;
                }
                var filereader = new FileReader();
                filereader.readAsDataURL(file);
                filereader.onloadend = function(upload) {
                        var data = upload.target.result;
                        data64 = data.split(',')[1];
                        var values = {
                            'name' : file.name,
                            'type' : 'binary',
                            'datas' : data64,
                        };
                        values_list.push([ 0, 0, values]);
                        if(values_list.length == files.length){
                            attachment_ids.set_value(values_list);
                        }
                };
            });
        },
        already_attached : function (attachments,filename) {
              for(var i=0;i<attachments.length;i++){
                  if(attachments[i][2]['name'] == filename){
                      return true;
                  }
              }
              return false;
        },
    });

    core.form_widget_registry.add('import_files_button',import_files_button);

});