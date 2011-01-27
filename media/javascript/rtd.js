 $(document).ready(function()
 {
    ShowActionOnOver();
 });

 function ShowActionOnOver()
 {
   $(".module-item-menu").hover(
       function()
       {
          $(".hidden-child",this).show();
       },
       function()
       {
           $(".hidden-child",this).hide();
        }
    );
 }
