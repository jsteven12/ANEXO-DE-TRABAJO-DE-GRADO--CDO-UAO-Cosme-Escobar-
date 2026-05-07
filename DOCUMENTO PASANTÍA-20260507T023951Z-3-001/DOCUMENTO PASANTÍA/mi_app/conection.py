from supabase import create_client, Client
from datetime import datetime
import hashlib
import secrets
import os

#Configuracion


SUPABASE_URL = "https://puivxckjypuyuoxmfsoa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1aXZ4Y2tqeXB1eXVveG1mc29hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0NTA0NDMsImV4cCI6MjA3NjAyNjQ0M30.ndNCHjGnP8T-MbHLd4BlUsZk6W-b149DEOSwNyrUvZw"


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ===== MÉTODO 1: Verificación Básica =====
def verificar_conexion_basica():
    """Verifica si las credenciales son correctas"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Cliente de Supabase creado exitosamente")
        return supabase
    except Exception as e:
        print(f"❌ Error al crear cliente: {e}")
        return None


# ===== MÉTODO 2: Verificación con Consulta Simple =====
def verificar_conexion_completa():
    """Verifica la conexión haciendo una consulta real"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Intenta hacer una consulta simple (listar tablas disponibles)
        # Esta consulta funciona incluso si no hay tablas
        response = supabase.table("usuarios").select("count", count="exact").execute()
        
        print("✅ Conexión exitosa con Supabase")
        print(f"   📊 Registros en tabla 'usuarios': {response.count}")
        return supabase
        
    except Exception as e:
        error_msg = str(e)
        
        if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
            print("⚠️  Conexión exitosa, pero la tabla 'usuarios' no existe")
            print("   💡 Necesitas crear la tabla primero")
            return supabase
        elif "JWT" in error_msg or "authentication" in error_msg.lower():
            print("❌ Error de autenticación: Verifica tu SUPABASE_KEY")
        elif "url" in error_msg.lower() or "host" in error_msg.lower():
            print("❌ Error de URL: Verifica tu SUPABASE_URL")
        else:
            print(f"❌ Error de conexión: {e}")
        
        return None


# ===== MÉTODO 3: Verificación Detallada =====
def verificar_conexion_detallada():
    """Verificación completa con información detallada"""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO CONEXIÓN A SUPABASE")
    print("="*60)
    
    # 1. Verificar que las credenciales no estén vacías
    print("\n1️⃣ Verificando credenciales...")
    if not SUPABASE_URL or SUPABASE_URL == "https://tu-proyecto.supabase.co":
        print("   ❌ SUPABASE_URL no configurada correctamente")
        return None
    if not SUPABASE_KEY or SUPABASE_KEY == "tu-anon-key-aqui":
        print("   ❌ SUPABASE_KEY no configurada correctamente")
        return None
    
    print(f"   ✅ URL: {SUPABASE_URL[:30]}...")
    print(f"   ✅ KEY: {SUPABASE_KEY[:20]}...")
    
    # 2. Crear cliente
    print("\n2️⃣ Creando cliente de Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   ✅ Cliente creado correctamente")
    except Exception as e:
        print(f"   ❌ Error al crear cliente: {e}")
        return None
    
    # 3. Probar conexión
    print("\n3️⃣ Probando conexión con base de datos...")
    try:
        # Intenta obtener la tabla usuarios
        response = supabase.table("usuarios").select("*").limit(1).execute()
        print("   ✅ Conexión exitosa")
        print(f"   📊 Tabla 'usuarios' accesible")
        
        if response.data:
            print(f"   📝 Ejemplo de registro encontrado")
        else:
            print(f"   📝 Tabla vacía (sin registros)")
        
        return supabase
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "relation" in error_msg or "does not exist" in error_msg:
            print("   ⚠️  Tabla 'usuarios' no existe")
            print("   💡 Conexión OK, pero necesitas crear la tabla")
            print("\n   📋 Ejecuta este SQL en Supabase:")
            print("   " + "-"*50)
            print("""
   CREATE TABLE usuarios (
     id BIGSERIAL PRIMARY KEY,
     nombre VARCHAR(100) NOT NULL,
     email VARCHAR(100) UNIQUE NOT NULL,
     password TEXT NOT NULL,
     activo BOOLEAN DEFAULT TRUE,
     fecha_desactivacion TIMESTAMP,
     motivo_desactivacion TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
            """)
            print("   " + "-"*50)
            return supabase
            
        elif "jwt" in error_msg or "authentication" in error_msg:
            print("   ❌ Error de autenticación")
            print("   💡 Verifica que tu SUPABASE_KEY sea correcta")
            print("   📍 Encuéntrala en: Settings → API → anon/public key")
            
        elif "url" in error_msg or "host" in error_msg or "resolve" in error_msg:
            print("   ❌ Error de URL")
            print("   💡 Verifica que tu SUPABASE_URL sea correcta")
            print("   📍 Formato: https://tu-proyecto.supabase.co")
            
        else:
            print(f"   ❌ Error desconocido: {e}")
        
        return None
    
    finally:
        print("\n" + "="*60 + "\n")


# ===== MÉTODO 4: Verificación con Health Check =====
def health_check():
    """Verifica el estado de la conexión y muestra estadísticas"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("\n" + "="*60)
        print("💚 HEALTH CHECK - SUPABASE")
        print("="*60)
        
        # Probar varias tablas comunes
        tablas_a_probar = ["usuarios"]
        
        for tabla in tablas_a_probar:
            try:
                response = supabase.table(tabla).select("*", count="exact").limit(0).execute()
                print(f"✅ Tabla '{tabla}': {response.count} registros")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print(f"⚠️  Tabla '{tabla}': No existe")
                else:
                    print(f"❌ Tabla '{tabla}': Error - {e}")
        
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Health Check falló: {e}\n")
        return False


# ===== MÉTODO 5: Auto-diagnóstico =====
def diagnostico_completo():
    """Diagnóstico automático de problemas comunes"""
    print("\n" + "🔧 DIAGNÓSTICO AUTOMÁTICO")
    print("="*60)
    
    problemas = []
    
    # Verificar URL
    if not SUPABASE_URL or "tu-proyecto" in SUPABASE_URL:
        problemas.append({
            "tipo": "URL no configurada",
            "solucion": "Reemplaza SUPABASE_URL con tu URL real de Supabase"
        })
    
    # Verificar KEY
    if not SUPABASE_KEY or "tu-anon-key" in SUPABASE_KEY:
        problemas.append({
            "tipo": "API Key no configurada",
            "solucion": "Reemplaza SUPABASE_KEY con tu API key de Supabase"
        })
    
    # Verificar formato de URL
    if SUPABASE_URL and not SUPABASE_URL.startswith("https://"):
        problemas.append({
            "tipo": "Formato de URL incorrecto",
            "solucion": "La URL debe empezar con https://"
        })
    
    # Verificar longitud de KEY
    if SUPABASE_KEY and len(SUPABASE_KEY) < 50:
        problemas.append({
            "tipo": "API Key sospechosamente corta",
            "solucion": "Verifica que copiaste la key completa"
        })
    
    if problemas:
        print("\n⚠️  PROBLEMAS DETECTADOS:\n")
        for i, problema in enumerate(problemas, 1):
            print(f"{i}. {problema['tipo']}")
            print(f"   💡 Solución: {problema['solucion']}\n")
        return False
    else:
        print("\n✅ No se detectaron problemas de configuración\n")
        return True


# ===== FUNCIÓN PRINCIPAL =====
def main():
    """Ejecuta todas las verificaciones"""
    
    # Diagnóstico previo
    if not diagnostico_completo():
        print("❌ Configura correctamente las credenciales antes de continuar\n")
        return
    
    # Verificación detallada
    supabase = verificar_conexion_detallada()
    
    if supabase:
        # Health check
        health_check()
        print("🎉 ¡Todo listo para usar Supabase!\n")
        return supabase
    else:
        print("❌ No se pudo establecer conexión con Supabase\n")
        print("📚 Recursos útiles:")
        print("   - Documentación: https://supabase.com/docs")
        print("   - Dashboard: https://app.supabase.com")
        return None


# ===== DECORADOR PARA USO EN OTRAS FUNCIONES =====
def requiere_conexion(func):
    """Decorador que verifica la conexión antes de ejecutar una función"""
    def wrapper(*args, **kwargs):
        try:
            # Intenta una operación simple
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            test = supabase.table("usuarios").select("*").limit(0).execute()
            return func(*args, **kwargs)
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            print("💡 Verifica tu conexión a Supabase")
            return None
    return wrapper


# Ejemplo de uso del decorador
@requiere_conexion
def mi_funcion_ejemplo():
    print("✅ Función ejecutada exitosamente")
    return True


# ===== EJECUTAR VERIFICACIÓN =====
if __name__ == "__main__":
    print("\n" + "🚀 INICIANDO VERIFICACIÓN DE CONEXIÓN A SUPABASE" + "\n")
    
    # Ejecutar verificación completa
    supabase_client = main()
    
    if supabase_client:
        print("✅ Puedes usar 'supabase_client' para tus operaciones")
    else:
        print("⚠️  Revisa la configuración y vuelve a intentar")