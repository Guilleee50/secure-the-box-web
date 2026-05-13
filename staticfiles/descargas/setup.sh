#!/bin/bash

# Script de instalación para Secure The Box en Ubuntu/Debian

# 1. Actualizar la lista de paquetes
echo "Actualizando la lista de paquetes..."
sudo apt update

# 2. Instalar dependencias del sistema
echo "Instalando dependencias del sistema (python3-tk, python3-venv, git, openssh-server, nano)..."
sudo apt install -y python3-tk python3-venv git openssh-server nano

# 3. Clonar o actualizar el repositorio de GitHub
REPO_DIR="secure-the-box"
REPO_URL="https://github.com/ikermoro28/secure-the-box.git"

if [ -d "$REPO_DIR" ]; then
    echo "El repositorio '$REPO_DIR' ya existe. Actualizando con git pull..."
    cd "$REPO_DIR"
    git pull
else
    echo "Clonando el repositorio '$REPO_DIR'..."
    git clone "$REPO_URL"
    # Verificar si la clonación fue exitosa
    if [ ! -d "$REPO_DIR" ]; then
        echo "Error: No se pudo clonar el repositorio. Saliendo."
        exit 1
    fi
    cd "$REPO_DIR"
fi

# 4. Crear un entorno virtual de Python
echo "Creando un entorno virtual de Python..."
python3 -m venv venv

# 5. Activar el entorno virtual
echo "Activando el entorno virtual..."
source venv/bin/activate

# 6. Instalar dependencias de Python
echo "Instalando dependencias de Python desde requirements.txt..."
pip install -r requirements.txt

# 7. Crear el acceso directo (.desktop) en el sistema del usuario
echo "Configurando el lanzador de la aplicación en Ubuntu..."
# Obtenemos la ruta absoluta del directorio actual (el repo)
APP_DIR=$(pwd)
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/secure-the-box.desktop"

# Nos aseguramos de que el directorio de aplicaciones existe
mkdir -p "$DESKTOP_DIR"

# Creamos el archivo de configuración usando las rutas absolutas y el Path
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Name=Secure The Box
Comment=Defensive CTF Trainer
Exec=$APP_DIR/venv/bin/python $APP_DIR/app.py
Path=$APP_DIR
Icon=$APP_DIR/logo.png
Terminal=false
Type=Application
Categories=Education;Utility;
EOF

# Le damos permisos de ejecución al lanzador
chmod +x "$DESKTOP_FILE"
echo "Lanzador creado con éxito."

# 8. Mensajes finales
echo -e "\nInstalación completada con éxito."
echo "¡Ya puedes buscar 'Secure The Box' en el menú de aplicaciones de Ubuntu para lanzarla directamente con su icono!"
echo -e "\nSi prefieres ejecutarla manualmente por terminal, navega al directorio del proyecto ($REPO_DIR) y ejecuta:"
echo "  source venv/bin/activate"
echo "  python3 app.py"
