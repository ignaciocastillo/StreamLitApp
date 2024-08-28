import streamlit as st  # type: ignore
import sqlite3
import pandas as pd  # type: ignore
import requests  # type: ignore


# Conectar a la base de datos SQLite (se creará si no existe)
conn = sqlite3.connect("erp_app.db")
cursor = conn.cursor()

# Crear las tablas si no existen
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo_electronico TEXT NOT NULL,
    segmento_negocio TEXT NOT NULL
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    total REAL NOT NULL,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    monto REAL NOT NULL
)
"""
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS factura_productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    monto REAL NOT NULL,
    FOREIGN KEY(factura_id) REFERENCES facturas(id),
    FOREIGN KEY(producto_id) REFERENCES productos(id)
)
"""
)
conn.commit()


# Funciones auxiliares para cargar y guardar datos
def cargar_clientes():
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    clientes_df = pd.DataFrame(
        clientes, columns=["ID", "Nombre", "Correo Electrónico", "Segmento de Negocio"]
    )
    return clientes_df


def agregar_cliente(nombre, correo, segmento):
    cursor.execute(
        "INSERT INTO clientes (nombre, correo_electronico, segmento_negocio) VALUES (?, ?, ?)",
        (nombre, correo, segmento),
    )
    conn.commit()
    return cursor.lastrowid


def actualizar_cliente(cliente_id, nombre, correo, segmento):
    cursor.execute(
        "UPDATE clientes SET nombre = ?, correo_electronico = ?, segmento_negocio = ? WHERE id = ?",
        (nombre, correo, segmento, cliente_id),
    )
    conn.commit()


def eliminar_cliente(cliente_id):
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()


def cargar_productos():
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    productos_df = pd.DataFrame(
        productos, columns=["ID", "Nombre", "Categoría", "Monto"]
    )
    return productos_df


def agregar_producto(nombre, categoria, monto):
    cursor.execute(
        "INSERT INTO productos (nombre, categoria, monto) VALUES (?, ?, ?)",
        (nombre, categoria, monto),
    )
    conn.commit()
    return cursor.lastrowid


def eliminar_producto(producto_id):
    cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()


def agregar_factura(cliente_id, total):
    cursor.execute(
        "INSERT INTO facturas (cliente_id, total) VALUES (?, ?)", (cliente_id, total)
    )
    conn.commit()
    return cursor.lastrowid


def agregar_factura_producto(factura_id, producto_id, cantidad, monto):
    cursor.execute(
        "INSERT INTO factura_productos (factura_id, producto_id, cantidad, monto) VALUES (?, ?, ?, ?)",
        (factura_id, producto_id, cantidad, monto),
    )
    conn.commit()


def generar_factura_api(cliente_nombre, cliente_correo, productos, total):
    url = "https://invoice-generator.com"
    api_key = "sk_yLqHnjWxZFirKYSBIhJpZq7gvHQzw4Ay"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    items = [
        {
            "name": prod["nombre"],
            "quantity": prod["cantidad"],
            "unit_cost": prod["monto"],
        }
        for prod in productos
    ]

    data = {
        "from": "FACTURA",
        "to": cliente_nombre,
        "logo": "https://example.com/img/logo-invoice.png",
        "number": 1,
        "items": items,
        "notes": "¡Gracias por su compra!",
        "currency": "CRC",  # Moneda configurada a Colones Costarricenses
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        with open("invoice.pdf", "wb") as f:
            f.write(response.content)
        return "invoice.pdf"
    else:
        st.error(
            f"Error al generar la factura: {response.status_code} - {response.text}"
        )
        return None


def get_random_quote():
    response = requests.get("https://www.tronalddump.io/random/quote")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error al obtener la cita.")
        return None


# Configuración de la aplicación Streamlit
st.set_page_config(layout="wide", page_icon="💻", page_title="Oliver Tech 🦮")
st.title("💻 OliverTech 🦮")

# Crear las pestañas
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    [
        "Listado de Clientes",
        "Agregar Cliente",
        "Actualizar o Eliminar Cliente",
        "Productos",
        "Facturar",
        "Chistín",
        "Generar datos prefabricados",
        "Borrar toda la base de datos",
    ]
)

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
    segmentos_df = (
        clientes_df["Segmento de Negocio"].drop_duplicates().tolist()
        if not clientes_df.empty
        else []
    )

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
        cliente_id = st.selectbox(
            "Selecciona un Cliente para Editar o Eliminar",
            clientes_df["ID"],
            format_func=lambda x: clientes_df.loc[
                clientes_df["ID"] == x, "Nombre"
            ].values[0],
        )
        cliente_seleccionado_df = clientes_df[clientes_df["ID"] == cliente_id]

        if not cliente_seleccionado_df.empty:
            cliente_seleccionado = cliente_seleccionado_df.iloc[0]

            # Formulario para actualizar el cliente
            with st.form("form_actualizar_cliente"):
                nuevo_nombre = st.text_input("Nombre", cliente_seleccionado["Nombre"])
                nuevo_correo = st.text_input(
                    "Correo Electrónico", cliente_seleccionado["Correo Electrónico"]
                )
                nuevo_segmento = st.text_input(
                    "Segmento de Negocio", cliente_seleccionado["Segmento de Negocio"]
                )
                actualizar_button = st.form_submit_button("Actualizar Cliente")

                if actualizar_button:
                    actualizar_cliente(
                        cliente_id, nuevo_nombre, nuevo_correo, nuevo_segmento
                    )
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
        producto_id = st.selectbox(
            "Selecciona un Producto para Eliminar",
            productos_df["ID"],
            format_func=lambda x: productos_df.loc[
                productos_df["ID"] == x, "Nombre"
            ].values[0],
        )
        eliminar_producto_button = st.button("Eliminar Producto")

        if eliminar_producto_button:
            eliminar_producto(producto_id)
            st.success("Producto eliminado exitosamente")


### **Pestaña: Facturar**
with tab5:
    st.subheader("Generar Factura")

    if "productos_temp" not in st.session_state:
        st.session_state.productos_temp = []

    clientes_df = cargar_clientes()
    if not clientes_df.empty:
        cliente_id = st.selectbox(
            "Selecciona un Cliente",
            clientes_df["ID"],
            format_func=lambda x: clientes_df.loc[
                clientes_df["ID"] == x, "Nombre"
            ].values[0],
        )
        cliente_seleccionado_df = clientes_df[clientes_df["ID"] == cliente_id].iloc[0]

        st.write(f"**Cliente:** {cliente_seleccionado_df['Nombre']}")
        st.write(f"**Correo:** {cliente_seleccionado_df['Correo Electrónico']}")
        st.write(f"**Segmento:** {cliente_seleccionado_df['Segmento de Negocio']}")

        productos_df = cargar_productos()
        if not productos_df.empty:
            with st.form("invoice_form"):
                producto_id = st.selectbox(
                    "Selecciona un Producto",
                    productos_df["ID"],
                    format_func=lambda x: productos_df.loc[
                        productos_df["ID"] == x, "Nombre"
                    ].values[0],
                )
                producto_seleccionado_df = productos_df[
                    productos_df["ID"] == producto_id
                ].iloc[0]

                producto_cantidad = st.number_input("Cantidad", min_value=1)
                agregar_producto_btn = st.form_submit_button("Agregar producto")

                if agregar_producto_btn:
                    st.session_state.productos_temp.append(
                        {
                            "nombre": producto_seleccionado_df["Nombre"],
                            "categoria": producto_seleccionado_df["Categoría"],
                            "monto": producto_seleccionado_df["Monto"],
                            "cantidad": producto_cantidad,
                        }
                    )

                if st.session_state.productos_temp:
                    st.write("### Productos agregados")
                    st.table(st.session_state.productos_temp)

                total = sum(
                    p["monto"] * p["cantidad"] for p in st.session_state.productos_temp
                )
                st.write(f"### Total: {total:.2f}")

                submit_invoice = st.form_submit_button("Generar factura")
                if submit_invoice:
                    factura_id = agregar_factura(cliente_id, total)

                    for producto in st.session_state.productos_temp:
                        producto_id = productos_df[
                            productos_df["Nombre"] == producto["nombre"]
                        ]["ID"].values[0]
                        agregar_factura_producto(
                            factura_id,
                            producto_id,
                            producto["cantidad"],
                            producto["monto"],
                        )

                    invoice_pdf = generar_factura_api(
                        cliente_seleccionado_df["Nombre"],
                        cliente_seleccionado_df["Correo Electrónico"],
                        st.session_state.productos_temp,
                        total,
                    )

                    if invoice_pdf:
                        st.session_state.invoice_pdf = invoice_pdf
                    st.success("Factura generada exitosamente")

                    st.session_state.productos_temp = []

        else:
            st.write("No hay productos disponibles para agregar a la factura.")
    else:
        st.write("No hay clientes disponibles. Por favor, agrega un cliente primero.")

if "invoice_pdf" in st.session_state:
    with open(st.session_state.invoice_pdf, "rb") as pdf_file:
        st.download_button(
            "Descargar Factura en PDF",
            data=pdf_file,
            file_name=st.session_state.invoice_pdf,
        )


def insertar_datos_de_ejemplo():
    # Aquí está el código que maneja la inserción de datos de ejemplo
    clientes = [
        ("Oficina Central", "oficina.central@example.com", "Corporativo"),
        ("Papelería Rápida", "papeleria.rapida@example.com", "Pequeño Negocio"),
        ("Tech Solutions", "tech.solutions@example.com", "Tecnología"),
        ("Diseños Creativos", "disenos.creativos@example.com", "Diseño Gráfico"),
        ("Consultores XYZ", "consultores.xyz@example.com", "Consultoría"),
        ("Ofiservicios", "ofiservicios@example.com", "Servicios"),
        ("Papel y Más", "papel.mas@example.com", "Papelería"),
        ("Digital Plus", "digital.plus@example.com", "Impresión"),
        ("Suministros Globales", "suministros.globales@example.com", "Importación"),
        ("ABC Oficina", "abc.oficina@example.com", "Corporativo"),
        ("Papelería Universal", "papeleria.universal@example.com", "Papelería"),
        ("Equipos de Oficina CR", "equipos.oficina.cr@example.com", "Retail"),
        ("Soluciones Integrales", "soluciones.integrales@example.com", "Consultoría"),
        ("MaxiOficina", "maxioficina@example.com", "Corporativo"),
        ("Servicios Empresariales", "servicios.empresariales@example.com", "Servicios"),
    ]
    for cliente in clientes:
        cursor.execute(
            "INSERT INTO clientes (nombre, correo_electronico, segmento_negocio) VALUES (?, ?, ?)",
            cliente,
        )

    productos = [
        ("Asrock X570 Phantom Gaming 4 WIFI AX", "Tarjetas Madre", 87000),
        ("G.SKILL Trident Z RGB 16 GB DDR4 3200 - Ryzen", "Memoria RAM", 24000),
        ("MSI B450M PRO-VDH MAX", "Tarjetas Madre", 42000),
        ("Aerocool Cylon 700W ARGB - 80 Plus Bronze", "Fuentes de Poder", 25000),
        ("AMD Athlon 3000G", "Procesadores", 43900),
        ("Adata HD330 2 TB USB 3.2", "Almacenamiento", 43900),
        ("NZXT Kraken Z63 - Pantalla LCD", "Enfriamiento Líquido", 119000),
        ("Seasonic Focus GX-850 - 80 Plus Gold", "Fuentes de Poder", 69000),
        ("Aerocool Eclipse 12 ARGB - 120mm PWM", "Ventiladores", 3500),
        ("Teamgroup MP33 1TB", "Almacenamiento", 32900),
        ("Corsair Vengeance LPX 16GB DDR4", "Memoria RAM", 29000),
        ("Asus ROG Strix B450-F Gaming", "Tarjetas Madre", 82000),
        ("Intel Core i5-10400F", "Procesadores", 125000),
        ("Samsung 970 EVO Plus 500GB", "Almacenamiento", 79000),
        ("Cooler Master Hyper 212 RGB", "Enfriamiento Líquido", 45000),
        ("Gigabyte B550 AORUS Elite", "Tarjetas Madre", 110000),
        ("WD Blue 1TB 3D NAND", "Almacenamiento", 60000),
        ("AMD Ryzen 5 3600", "Procesadores", 135000),
        ("Patriot Viper Steel 16GB DDR4", "Memoria RAM", 28000),
        ("MSI MPG B550 Gaming Plus", "Tarjetas Madre", 95000),
        ("Corsair H100i RGB Platinum", "Enfriamiento Líquido", 135000),
        ("Seagate BarraCuda 2TB", "Almacenamiento", 85000),
        ("Thermaltake Smart 600W", "Fuentes de Poder", 45000),
        ("Asus TUF Gaming X570-Plus", "Tarjetas Madre", 125000),
        ("G.SKILL Ripjaws V Series 16GB DDR4", "Memoria RAM", 32000),
        ("Intel Core i7-10700K", "Procesadores", 250000),
        ("Samsung 860 EVO 1TB", "Almacenamiento", 150000),
        ("DeepCool Gammaxx GTE V2", "Enfriamiento Líquido", 40000),
        ("Gigabyte X570 AORUS Elite", "Tarjetas Madre", 140000),
        ("Crucial MX500 1TB", "Almacenamiento", 135000),
        ("AMD Ryzen 7 3700X", "Procesadores", 270000),
        ("Corsair Vengeance RGB Pro 16GB DDR4", "Memoria RAM", 36000),
        ("MSI MEG X570 Unify", "Tarjetas Madre", 165000),
        ("NZXT H510", "Gabinetes", 70000),
        ("Gigabyte B450M DS3H", "Tarjetas Madre", 75000),
        ("Patriot Viper Elite 8GB DDR4", "Memoria RAM", 16000),
        ("Intel Core i9-10900K", "Procesadores", 370000),
        ("WD Black SN750 1TB NVMe", "Almacenamiento", 175000),
        ("Noctua NH-D15", "Enfriamiento Líquido", 90000),
        ("MSI B450 TOMAHAWK MAX", "Tarjetas Madre", 105000),
        ("Corsair RM750x", "Fuentes de Poder", 85000),
        ("Asus Prime B450M-A", "Tarjetas Madre", 68000),
        ("Adata XPG SX8200 Pro 1TB", "Almacenamiento", 150000),
        ("AMD Ryzen 9 3900X", "Procesadores", 370000),
        ("Corsair Vengeance LPX 32GB DDR4", "Memoria RAM", 58000),
        ("Asrock B450 Steel Legend", "Tarjetas Madre", 95000),
        ("Samsung 970 Pro 1TB", "Almacenamiento", 210000),
        ("Thermaltake Toughpower GF1 750W", "Fuentes de Poder", 90000),
        ("MSI MAG B550M Mortar", "Tarjetas Madre", 100000),
        ("Intel Core i5-10600K", "Procesadores", 160000),
        ("Patriot Burst 480GB SSD", "Almacenamiento", 45000),
        ("NZXT Kraken X53", "Enfriamiento Líquido", 130000),
        ("Gigabyte Z490 AORUS Ultra", "Tarjetas Madre", 225000),
        ("Crucial Ballistix 16GB DDR4", "Memoria RAM", 33000),
        ("AMD Ryzen 5 5600X", "Procesadores", 190000),
        ("WD Blue SN550 500GB", "Almacenamiento", 80000),
        ("Corsair SF600", "Fuentes de Poder", 110000),
        ("Asus ROG Strix B550-F Gaming", "Tarjetas Madre", 150000),
        ("Samsung 860 QVO 1TB", "Almacenamiento", 130000),
        ("Cooler Master MasterLiquid ML240L", "Enfriamiento Líquido", 100000),
        ("MSI MPG Z490 Gaming Edge", "Tarjetas Madre", 185000),
        ("G.SKILL Trident Z Neo 16GB DDR4", "Memoria RAM", 42000),
        ("Intel Core i9-11900K", "Procesadores", 400000),
        ("TeamGroup T-Force Vulcan Z 1TB", "Almacenamiento", 140000),
        ("Thermaltake Smart BX1 650W", "Fuentes de Poder", 55000),
        ("Gigabyte Z390 AORUS Pro", "Tarjetas Madre", 180000),
        ("Patriot P300 512GB", "Almacenamiento", 70000),
        ("AMD Ryzen 7 5800X", "Procesadores", 320000),
        ("Corsair Dominator Platinum 16GB DDR4", "Memoria RAM", 45000),
        ("Asrock X570 Taichi", "Tarjetas Madre", 180000),
        ("Samsung 980 Pro 1TB", "Almacenamiento", 250000),
        ("Cooler Master V850 Gold", "Fuentes de Poder", 125000),
        ("MSI MEG Z490 ACE", "Tarjetas Madre", 240000),
        ("Intel Core i7-11700K", "Procesadores", 290000),
        ("WD Blue 4TB HDD", "Almacenamiento", 200000),
        ("NZXT H710", "Gabinetes", 130000),
        ("Asus TUF Gaming B550M-PLUS", "Tarjetas Madre", 110000),
        ("Adata XPG Gammix S11 Pro 1TB", "Almacenamiento", 165000),
        ("Corsair AX860", "Fuentes de Poder", 145000),
        ("Gigabyte Z490 Vision G", "Tarjetas Madre", 190000),
        ("AMD Ryzen 9 5950X", "Procesadores", 620000),
        ("TeamGroup T-Force Delta RGB 32GB DDR4", "Memoria RAM", 90000),
        ("MSI MPG Z490 Gaming Carbon", "Tarjetas Madre", 210000),
        ("Samsung 870 QVO 1TB", "Almacenamiento", 120000),
        ("Corsair CX550M", "Fuentes de Poder", 65000),
        ("Asrock B550 Phantom Gaming 4", "Tarjetas Madre", 90000),
        ("Patriot Viper VPN100 512GB NVMe", "Almacenamiento", 95000),
        ("Intel Core i5-11600K", "Procesadores", 170000),
        ("Cooler Master MasterBox Q300L", "Gabinetes", 45000),
    ]

    for producto in productos:
        cursor.execute(
            "INSERT INTO productos (nombre, categoria, monto) VALUES (?, ?, ?)",
            producto,
        )

    facturas = [
        (1, 155000.00),
        (2, 234000.00),
        (3, 560000.00),
        (4, 650000.00),
        (5, 82000.00),
    ]
    for factura in facturas:
        cursor.execute(
            "INSERT INTO facturas (cliente_id, total) VALUES (?, ?)", factura
        )

    factura_productos = [
        (1, 1, 2, 174000.00),
        (1, 2, 4, 96000.00),
        (2, 3, 2, 84000.00),
        (3, 4, 3, 75000.00),
        (4, 5, 1, 43900.00),
    ]
    for fp in factura_productos:
        cursor.execute(
            "INSERT INTO factura_productos (factura_id, producto_id, cantidad, monto) VALUES (?, ?, ?, ?)",
            fp,
        )

    conn.commit()
    st.success("Datos de ejemplo insertados correctamente.")


### **Pestaña: Chistín (Citas Aleatorias de Tronald Dump)**
with tab6:
    st.title("Citas de Tronald Dump")

    # Botón para obtener una cita aleatoria
    if st.button("Obtener una cita aleatoria"):
        quote = get_random_quote()
        if quote:
            st.write(f"Cita: {quote['value']}")
            st.write(f"Fecha: {quote['appeared_at']}")


with tab7:
    st.title("Generar Datos de Ejemplo")
    if st.button("Generar Datos de Ejemplo"):
        insertar_datos_de_ejemplo()
        st.success("Datos de ejemplo generados exitosamente.")


def reset_database():
    cursor.execute("DELETE FROM factura_productos")
    cursor.execute("DELETE FROM facturas")
    cursor.execute("DELETE FROM productos")
    cursor.execute("DELETE FROM clientes")
    conn.commit()


with tab8:
    # Botón para resetear la base de datos
    if st.button("Resetear Base de Datos"):
        reset_database()
        st.warning("¡Todos los datos han sido eliminados!")
