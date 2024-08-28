import streamlit as st
import sqlite3
import pandas as pd
import requests

# Conectar a la base de datos SQLite (se creará si no existe)
conn = sqlite3.connect('erp_app.db')
cursor = conn.cursor()

# Crear las tablas si no existen
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo_electronico TEXT NOT NULL,
    segmento_negocio TEXT NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    total REAL NOT NULL,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    monto REAL NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS factura_productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    monto REAL NOT NULL,
    FOREIGN KEY(factura_id) REFERENCES facturas(id),
    FOREIGN KEY(producto_id) REFERENCES productos(id)
)
''')
conn.commit()

# Funciones auxiliares para cargar y guardar datos
def cargar_clientes():
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    clientes_df = pd.DataFrame(clientes, columns=["ID", "Nombre", "Correo Electrónico", "Segmento de Negocio"])
    return clientes_df

def agregar_cliente(nombre, correo, segmento):
    cursor.execute("INSERT INTO clientes (nombre, correo_electronico, segmento_negocio) VALUES (?, ?, ?)",
                   (nombre, correo, segmento))
    conn.commit()
    return cursor.lastrowid

def actualizar_cliente(cliente_id, nombre, correo, segmento):
    cursor.execute("UPDATE clientes SET nombre = ?, correo_electronico = ?, segmento_negocio = ? WHERE id = ?",
                   (nombre, correo, segmento, cliente_id))
    conn.commit()

def eliminar_cliente(cliente_id):
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()

def cargar_productos():
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    productos_df = pd.DataFrame(productos, columns=["ID", "Nombre", "Categoría", "Monto"])
    return productos_df

def agregar_producto(nombre, categoria, monto):
    cursor.execute("INSERT INTO productos (nombre, categoria, monto) VALUES (?, ?, ?)",
                   (nombre, categoria, monto))
    conn.commit()
    return cursor.lastrowid

def eliminar_producto(producto_id):
    cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()

def agregar_factura(cliente_id, total):
    cursor.execute("INSERT INTO facturas (cliente_id, total) VALUES (?, ?)", (cliente_id, total))
    conn.commit()
    return cursor.lastrowid

def agregar_factura_producto(factura_id, producto_id, cantidad, monto):
    cursor.execute("INSERT INTO factura_productos (factura_id, producto_id, cantidad, monto) VALUES (?, ?, ?, ?)",
                   (factura_id, producto_id, cantidad, monto))
    conn.commit()

def generar_factura_api(cliente_nombre, cliente_correo, productos, total):
    url = "https://invoice-generator.com"
    api_key = "sk_yLqHnjWxZFirKYSBIhJpZq7gvHQzw4Ay" 
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    items = [{"name": prod["nombre"], "quantity": prod["cantidad"], "unit_cost": prod["monto"]} for prod in productos]
    
    data = {
        "from": "Profe Mauro y el otro mae no hicieron nada. - Los Castillo Vega",
        "to": cliente_nombre,
        "logo": "https://example.com/img/logo-invoice.png", 
        "number": 1,
        "items": items,
        "notes": "¡Gracias por su compra!",
        "currency": "CRC"  # Moneda configurada a Colones Costarricenses
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        with open("invoice.pdf", "wb") as f:
            f.write(response.content)
        return "invoice.pdf"
    else:
        st.error(f"Error al generar la factura: {response.status_code} - {response.text}")
        return None

def get_random_quote():
    response = requests.get("https://www.tronalddump.io/random/quote")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error al obtener la cita.")
        return None

# Configuración de la aplicación Streamlit
st.set_page_config(layout="centered", page_icon="💰", page_title="ERP Application")
st.title("💰 ERP Application")

# Crear las pestañas
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Listado de Clientes", "Agregar Cliente", "Actualizar o Eliminar Cliente", "Productos", "Facturar", "Chistín"])

### **Pestaña: Listado de Clientes**
with tab1:
    st.subheader("Listado de Clientes")
    clientes_df = cargar_clientes()
    if not clientes_df.empty:
        st.dataframe(clientes_df)
    else:
        st.write("No hay clientes registrados.")

### **Pestaña: Agregar Cliente**
with tab2:
    st.subheader("Agregar Cliente")
    segmentos_df = clientes_df["Segmento de Negocio"].drop_duplicates().tolist() if not clientes_df.empty else []
    
    with st.form("form_agregar_cliente"):
        nombre = st.text_input("Nombre")
        correo = st.text_input("Correo Electrónico")
        segmento = st.selectbox("Segmento de Negocio", segmentos_df + ["Otro..."])
        
        if segmento == "Otro...":
            segmento = st.text_input("Nuevo Segmento de Negocio")
        
        submit_button = st.form_submit_button("Agregar")
        if submit_button:
            if nombre and correo and segmento:
                cliente_id = agregar_cliente(nombre, correo, segmento)
                st.success("Cliente agregado exitosamente")
            else:
                st.error("Todos los campos son obligatorios")

### **Pestaña: Actualizar o Eliminar Cliente**
with tab3:
    st.subheader("Actualizar o Eliminar Cliente")
    clientes_df = cargar_clientes()
    if not clientes_df.empty:
        cliente_id = st.selectbox("Selecciona un Cliente para Editar o Eliminar", clientes_df["ID"], format_func=lambda x: clientes_df.loc[clientes_df["ID"] == x, "Nombre"].values[0])
        cliente_seleccionado_df = clientes_df[clientes_df["ID"] == cliente_id]

        if not cliente_seleccionado_df.empty:
            cliente_seleccionado = cliente_seleccionado_df.iloc[0]

            # Formulario para actualizar el cliente
            with st.form("form_actualizar_cliente"):
                nuevo_nombre = st.text_input("Nombre", cliente_seleccionado["Nombre"])
                nuevo_correo = st.text_input("Correo Electrónico", cliente_seleccionado["Correo Electrónico"])
                nuevo_segmento = st.text_input("Segmento de Negocio", cliente_seleccionado["Segmento de Negocio"])
                actualizar_button = st.form_submit_button("Actualizar Cliente")
                
                if actualizar_button:
                    actualizar_cliente(cliente_id, nuevo_nombre, nuevo_correo, nuevo_segmento)
                    st.success("Cliente actualizado exitosamente")
            
            # Formulario separado para eliminar el cliente
            with st.form("form_eliminar_cliente"):
                eliminar_button = st.form_submit_button("Eliminar Cliente")
                
                if eliminar_button:
                    eliminar_cliente(cliente_id)
                    st.success("Cliente eliminado exitosamente")
        else:
            st.error("El cliente seleccionado no existe.")
    else:
        st.write("No hay clientes disponibles para actualizar o eliminar.")

### **Pestaña: Productos**
with tab4:
    st.subheader("Gestión de Productos")
    
    productos_df = cargar_productos()
    if not productos_df.empty:
        st.dataframe(productos_df)
    
    with st.form("form_agregar_producto"):
        producto_nombre = st.text_input("Nombre del Producto")
        producto_categoria = st.text_input("Categoría")
        producto_monto = st.number_input("Monto", min_value=0.0, format="%.2f")
        submit_producto_button = st.form_submit_button("Agregar Producto")

        if submit_producto_button:
            if producto_nombre and producto_categoria and producto_monto:
                agregar_producto(producto_nombre, producto_categoria, producto_monto)
                st.success("Producto agregado exitosamente")
            else:
                st.error("Todos los campos son obligatorios")

    if not productos_df.empty:
        producto_id = st.selectbox("Selecciona un Producto para Eliminar", productos_df["ID"], format_func=lambda x: productos_df.loc[productos_df["ID"] == x, "Nombre"].values[0])
        eliminar_producto_button = st.button("Eliminar Producto")

        if eliminar_producto_button:
            eliminar_producto(producto_id)
            st.success("Producto eliminado exitosamente")

### **Pestaña: Facturar**
with tab5:
    st.subheader("Generar Factura")
    
    if 'productos_temp' not in st.session_state:
        st.session_state.productos_temp = []

    clientes_df = cargar_clientes()
    if not clientes_df.empty:
        cliente_id = st.selectbox("Selecciona un Cliente", clientes_df["ID"], format_func=lambda x: clientes_df.loc[clientes_df["ID"] == x, "Nombre"].values[0])
        cliente_seleccionado_df = clientes_df[clientes_df["ID"] == cliente_id].iloc[0]
        
        st.write(f"**Cliente:** {cliente_seleccionado_df['Nombre']}")
        st.write(f"**Correo:** {cliente_seleccionado_df['Correo Electrónico']}")
        st.write(f"**Segmento:** {cliente_seleccionado_df['Segmento de Negocio']}")
        
        productos_df = cargar_productos()
        if not productos_df.empty:
            with st.form("invoice_form"):
                producto_id = st.selectbox("Selecciona un Producto", productos_df["ID"], format_func=lambda x: productos_df.loc[productos_df["ID"] == x, "Nombre"].values[0])
                producto_seleccionado_df = productos_df[productos_df["ID"] == producto_id].iloc[0]

                producto_cantidad = st.number_input("Cantidad", min_value=1)
                agregar_producto_btn = st.form_submit_button("Agregar producto")

                if agregar_producto_btn:
                    st.session_state.productos_temp.append({
                        "nombre": producto_seleccionado_df["Nombre"],
                        "categoria": producto_seleccionado_df["Categoría"],
                        "monto": producto_seleccionado_df["Monto"],
                        "cantidad": producto_cantidad
                    })

                if st.session_state.productos_temp:
                    st.write("### Productos agregados")
                    st.table(st.session_state.productos_temp)

                total = sum(p["monto"] * p["cantidad"] for p in st.session_state.productos_temp)
                st.write(f"### Total: {total:.2f}")

                submit_invoice = st.form_submit_button("Generar factura")
                if submit_invoice:
                    factura_id = agregar_factura(cliente_id, total)

                    for producto in st.session_state.productos_temp:
                        producto_id = productos_df[productos_df["Nombre"] == producto["nombre"]]["ID"].values[0]
                        agregar_factura_producto(factura_id, producto_id, producto["cantidad"], producto["monto"])

                    invoice_pdf = generar_factura_api(cliente_seleccionado_df["Nombre"], cliente_seleccionado_df["Correo Electrónico"], st.session_state.productos_temp, total)
                    
                    if invoice_pdf:
                        st.session_state.invoice_pdf = invoice_pdf
                    st.success("Factura generada exitosamente")
                    st.session_state.productos_temp = []

        else:
            st.write("No hay productos disponibles para agregar a la factura.")
    else:
        st.write("No hay clientes disponibles. Por favor, agrega un cliente primero.")

if 'invoice_pdf' in st.session_state:
    with open(st.session_state.invoice_pdf, "rb") as pdf_file:
        st.download_button("Descargar Factura en PDF", data=pdf_file, file_name=st.session_state.invoice_pdf)

### **Pestaña: Chistín (Citas Aleatorias de Tronald Dump)**
with tab6:
    st.title("Citas de Tronald Dump")
    if st.button("Obtener una cita aleatoria"):
        quote = get_random_quote()
        if quote:
            st.write(f"Cita: {quote['value']}")
            st.write(f"Fecha: {quote['appeared_at']}")
 