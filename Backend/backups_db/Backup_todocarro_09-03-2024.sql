-- MySQL dump 10.13  Distrib 8.0.33, for Win64 (x86_64)
--
-- Host: localhost    Database: todocarro
-- ------------------------------------------------------
-- Server version	8.0.33

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `carritos`
--

DROP TABLE IF EXISTS `carritos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `carritos` (
  `carrito_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'activo, abandonado, completado',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`carrito_id`),
  KEY `fk_carritos_usuarios_idx` (`usuario_id`),
  CONSTRAINT `fk_carritos_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carritos`
--

LOCK TABLES `carritos` WRITE;
/*!40000 ALTER TABLE `carritos` DISABLE KEYS */;
/*!40000 ALTER TABLE `carritos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `carritos_productos`
--

DROP TABLE IF EXISTS `carritos_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `carritos_productos` (
  `carrito_producto_id` int NOT NULL AUTO_INCREMENT,
  `carrito_id` int NOT NULL,
  `producto_id` int NOT NULL,
  PRIMARY KEY (`carrito_producto_id`),
  KEY `fk_carritos_productos_carritos_idx` (`carrito_id`),
  KEY `fk_carritos_productos_productos_idx` (`producto_id`),
  CONSTRAINT `fk_carritos_productos_carritos` FOREIGN KEY (`carrito_id`) REFERENCES `carritos` (`carrito_id`),
  CONSTRAINT `fk_carritos_productos_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`producto_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carritos_productos`
--

LOCK TABLES `carritos_productos` WRITE;
/*!40000 ALTER TABLE `carritos_productos` DISABLE KEYS */;
/*!40000 ALTER TABLE `carritos_productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias` (
  `categoria_id` int NOT NULL AUTO_INCREMENT,
  `nombre_categoria` varchar(30) NOT NULL,
  `descripcion_categoria` text NOT NULL,
  PRIMARY KEY (`categoria_id`),
  UNIQUE KEY `nombre_categoria_UNIQUE` (`nombre_categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorias`
--

LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES (1,'Dirección','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(2,'Transmisión','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(3,'Suspensión','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(4,'Frenos','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(5,'Eléctrica','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(6,'Electrónica','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(7,'Refrigeración','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.'),(8,'Lubricación','El Lorem Ipsum fue concebido como un texto de relleno, formateado de una cierta manera para permitir la presentación de elementos gráficos en documentos.');
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_carritos`
--

DROP TABLE IF EXISTS `detalle_carritos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_carritos` (
  `detalle_carrito_id` int NOT NULL AUTO_INCREMENT,
  `carrito_id` int NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario` int NOT NULL,
  `subtotal` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`detalle_carrito_id`),
  KEY `fk_detalle_carritos_carritos_idx` (`carrito_id`),
  CONSTRAINT `fk_detalle_carritos_carritos` FOREIGN KEY (`carrito_id`) REFERENCES `carritos` (`carrito_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_carritos`
--

LOCK TABLES `detalle_carritos` WRITE;
/*!40000 ALTER TABLE `detalle_carritos` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalle_carritos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_ordenes`
--

DROP TABLE IF EXISTS `detalle_ordenes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_ordenes` (
  `detalle_orden_id` int NOT NULL AUTO_INCREMENT,
  `orden_id` int NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario` int NOT NULL,
  `subtotal` int NOT NULL,
  PRIMARY KEY (`detalle_orden_id`),
  KEY `fk_detalle_ordenes_ordenes_idx` (`orden_id`),
  CONSTRAINT `fk_detalle_ordenes_ordenes` FOREIGN KEY (`orden_id`) REFERENCES `ordenes` (`orden_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_ordenes`
--

LOCK TABLES `detalle_ordenes` WRITE;
/*!40000 ALTER TABLE `detalle_ordenes` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalle_ordenes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `domicilios`
--

DROP TABLE IF EXISTS `domicilios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `domicilios` (
  `domicilio_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `ciudad` varchar(15) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `direccion` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `referencia` varchar(40) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  PRIMARY KEY (`domicilio_id`),
  KEY `fk_domicilios_usuarios_idx` (`usuario_id`),
  CONSTRAINT `fk_domicilios_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `domicilios`
--

LOCK TABLES `domicilios` WRITE;
/*!40000 ALTER TABLE `domicilios` DISABLE KEYS */;
/*!40000 ALTER TABLE `domicilios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `envios`
--

DROP TABLE IF EXISTS `envios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `envios` (
  `envio_id` int NOT NULL AUTO_INCREMENT,
  `orden_id` int NOT NULL,
  `empresa_envio` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `numero_seguimiento` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `fecha_envio` datetime NOT NULL,
  `direccion_envio` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  PRIMARY KEY (`envio_id`),
  UNIQUE KEY `numero_seguimiento_UNIQUE` (`numero_seguimiento`),
  KEY `fk_envios_ordenes_idx` (`orden_id`),
  CONSTRAINT `fk_envios_ordenes` FOREIGN KEY (`orden_id`) REFERENCES `ordenes` (`orden_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `envios`
--

LOCK TABLES `envios` WRITE;
/*!40000 ALTER TABLE `envios` DISABLE KEYS */;
/*!40000 ALTER TABLE `envios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `facturas`
--

DROP TABLE IF EXISTS `facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facturas` (
  `factura_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `detalle_orden_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`factura_id`),
  KEY `fk_facturas_usuarios_idx` (`usuario_id`),
  KEY `fk_facturas_detalle_ordenes_idx` (`detalle_orden_id`),
  CONSTRAINT `fk_facturas_detalle_ordenes` FOREIGN KEY (`detalle_orden_id`) REFERENCES `detalle_ordenes` (`detalle_orden_id`),
  CONSTRAINT `fk_facturas_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `facturas`
--

LOCK TABLES `facturas` WRITE;
/*!40000 ALTER TABLE `facturas` DISABLE KEYS */;
/*!40000 ALTER TABLE `facturas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marcas`
--

DROP TABLE IF EXISTS `marcas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marcas` (
  `marca_id` int NOT NULL AUTO_INCREMENT,
  `nombre_marca` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL,
  PRIMARY KEY (`marca_id`),
  UNIQUE KEY `nombre_marca_UNIQUE` (`nombre_marca`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marcas`
--

LOCK TABLES `marcas` WRITE;
/*!40000 ALTER TABLE `marcas` DISABLE KEYS */;
INSERT INTO `marcas` VALUES (3,'Chevrolet'),(5,'Hyundai'),(10,'Kia'),(9,'Mazda'),(4,'Nissan'),(1,'Toyota');
/*!40000 ALTER TABLE `marcas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `metodos_pago`
--

DROP TABLE IF EXISTS `metodos_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `metodos_pago` (
  `met_pago_id` int NOT NULL AUTO_INCREMENT,
  `nombre_metodo_pago` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL COMMENT 'tarjeta de crédito, PayPal, transferencia bancaria, etc',
  `info_adicional` text COLLATE utf8mb3_spanish_ci NOT NULL,
  PRIMARY KEY (`met_pago_id`),
  UNIQUE KEY `nombre_metodo_pago_UNIQUE` (`nombre_metodo_pago`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `metodos_pago`
--

LOCK TABLES `metodos_pago` WRITE;
/*!40000 ALTER TABLE `metodos_pago` DISABLE KEYS */;
INSERT INTO `metodos_pago` VALUES (2,'Tarjeta de crédito/débito','Lorem Ipsum ha sido el texto de adabdja jadaj ajda ajdbajd afdadf final.'),(3,'PayPal','Una plataforma de pagos en línea que permite a los usuarios enviar y recibir pagos de forma segura a través de su cuenta bancaria o tarjeta de crédito.'),(4,'Transferencia bancaria','Los clientes pueden realizar pagos directamente desde su cuenta bancaria a la cuenta bancaria de la tienda.');
/*!40000 ALTER TABLE `metodos_pago` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modelos`
--

DROP TABLE IF EXISTS `modelos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `modelos` (
  `modelo_id` int NOT NULL AUTO_INCREMENT,
  `nombre_modelo` varchar(20) NOT NULL,
  `year_model` int NOT NULL,
  `marca_id` int NOT NULL,
  PRIMARY KEY (`modelo_id`),
  UNIQUE KEY `nombre_modelo_UNIQUE` (`nombre_modelo`),
  KEY `fk_modelos_marcas_idx` (`marca_id`),
  CONSTRAINT `fk_modelos_marcas` FOREIGN KEY (`marca_id`) REFERENCES `marcas` (`marca_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modelos`
--

LOCK TABLES `modelos` WRITE;
/*!40000 ALTER TABLE `modelos` DISABLE KEYS */;
/*!40000 ALTER TABLE `modelos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordenes`
--

DROP TABLE IF EXISTS `ordenes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordenes` (
  `orden_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `fecha_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  `direccion_domicilio` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `metodo_pago` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `status` varchar(15) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `total` int NOT NULL,
  PRIMARY KEY (`orden_id`),
  KEY `fk_ordenes_usuarios_idx` (`usuario_id`),
  CONSTRAINT `fk_ordenes_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordenes`
--

LOCK TABLES `ordenes` WRITE;
/*!40000 ALTER TABLE `ordenes` DISABLE KEYS */;
/*!40000 ALTER TABLE `ordenes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos`
--

DROP TABLE IF EXISTS `productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos` (
  `producto_id` int NOT NULL AUTO_INCREMENT,
  `titulo` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL,
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL,
  `imagen` varchar(40) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL,
  `price` int NOT NULL,
  `stock` int NOT NULL,
  `peso_kg` decimal(10,1) NOT NULL,
  `categoria_id` int NOT NULL,
  `marca_id` int NOT NULL,
  `model_id` int NOT NULL,
  `status` tinyint NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`producto_id`),
  UNIQUE KEY `titulo_UNIQUE` (`titulo`),
  KEY `fk_productos_categorias_idx` (`categoria_id`),
  KEY `fk_productos_marcas_idx` (`marca_id`),
  CONSTRAINT `fk_productos_categorias` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`categoria_id`),
  CONSTRAINT `fk_productos_marcas` FOREIGN KEY (`marca_id`) REFERENCES `marcas` (`marca_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos`
--

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos_detalle_carritos`
--

DROP TABLE IF EXISTS `productos_detalle_carritos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos_detalle_carritos` (
  `producto_detalle_carritos_id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `detalle_carrito_id` int NOT NULL,
  PRIMARY KEY (`producto_detalle_carritos_id`),
  KEY `fk_productos_detalle_carritos_productos_idx` (`producto_id`),
  KEY `fk_productos_detalle_carritos_detalle_carritos_idx` (`detalle_carrito_id`),
  CONSTRAINT `fk_productos_detalle_carritos_detalle_carritos` FOREIGN KEY (`detalle_carrito_id`) REFERENCES `detalle_carritos` (`detalle_carrito_id`),
  CONSTRAINT `fk_productos_detalle_carritos_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`producto_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos_detalle_carritos`
--

LOCK TABLES `productos_detalle_carritos` WRITE;
/*!40000 ALTER TABLE `productos_detalle_carritos` DISABLE KEYS */;
/*!40000 ALTER TABLE `productos_detalle_carritos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos_detalle_ordenes`
--

DROP TABLE IF EXISTS `productos_detalle_ordenes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos_detalle_ordenes` (
  `productos_detalle_ordenes_id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `detalle_orden_id` int NOT NULL,
  PRIMARY KEY (`productos_detalle_ordenes_id`),
  KEY `fk_productos_productos_detalle_ordenes_idx` (`producto_id`),
  KEY `fk_productos_detalle_ordenes_detalle_ordenes_idx` (`detalle_orden_id`),
  CONSTRAINT `fk_productos_detalle_ordenes_detalle_ordenes` FOREIGN KEY (`detalle_orden_id`) REFERENCES `detalle_ordenes` (`detalle_orden_id`),
  CONSTRAINT `fk_productos_detalle_ordenes_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`producto_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos_detalle_ordenes`
--

LOCK TABLES `productos_detalle_ordenes` WRITE;
/*!40000 ALTER TABLE `productos_detalle_ordenes` DISABLE KEYS */;
/*!40000 ALTER TABLE `productos_detalle_ordenes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos_marcas`
--

DROP TABLE IF EXISTS `productos_marcas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos_marcas` (
  `productos_marcas_id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `marca_id` int NOT NULL,
  PRIMARY KEY (`productos_marcas_id`),
  KEY `fk_productos_marcas_productos_idx` (`producto_id`),
  KEY `fk_productos_marcas_marcas_idx` (`marca_id`),
  CONSTRAINT `fk_productos_marcas_marcas` FOREIGN KEY (`marca_id`) REFERENCES `marcas` (`marca_id`),
  CONSTRAINT `fk_productos_marcas_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`producto_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos_marcas`
--

LOCK TABLES `productos_marcas` WRITE;
/*!40000 ALTER TABLE `productos_marcas` DISABLE KEYS */;
/*!40000 ALTER TABLE `productos_marcas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `rol_id` int NOT NULL AUTO_INCREMENT,
  `nombre_rol` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL COMMENT 'admin, cliente',
  PRIMARY KEY (`rol_id`),
  UNIQUE KEY `nombre_rol_UNIQUE` (`nombre_rol`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'administrador'),(2,'cliente');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario_productos`
--

DROP TABLE IF EXISTS `usuario_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario_productos` (
  `usuario_productos_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `producto_id` int NOT NULL,
  PRIMARY KEY (`usuario_productos_id`),
  KEY `fk_usuario_productos_productos_idx` (`producto_id`),
  KEY `fk_usuario_productos_usuarios_idx` (`usuario_id`),
  CONSTRAINT `fk_usuario_productos_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`producto_id`),
  CONSTRAINT `fk_usuario_productos_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario_productos`
--

LOCK TABLES `usuario_productos` WRITE;
/*!40000 ALTER TABLE `usuario_productos` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuario_productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `usuario_id` int NOT NULL AUTO_INCREMENT,
  `firstname` varchar(30) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci NOT NULL,
  `lastname` varchar(40) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `password` varchar(32) NOT NULL,
  `email` varchar(40) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `phonenumber` varchar(15) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `foto` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_spanish_ci DEFAULT NULL,
  `rol_id` int NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`),
  UNIQUE KEY `password_UNIQUE` (`password`),
  UNIQUE KEY `email_UNIQUE` (`email`),
  UNIQUE KEY `phonenumber_UNIQUE` (`phonenumber`),
  KEY `fk_usuarios_roles_idx` (`rol_id`),
  CONSTRAINT `fk_usuarios_roles` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`rol_id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (27,'Adolfo','Betin','FFP14QQY2XF','volutpat.nulla@hotmail.net','302-085-83-56','https://walmart.com/group/9',1,'2024-02-26 13:30:10'),(28,'Jonathan','Hernandez','XBL29DMD3GB','nascetur.ridiculus.mus@outlook.couk','302-283-14-37','http://cnn.com/settings',1,'2024-02-26 13:30:10'),(29,'Cruz','Key','PXU43JHD7BQ','luctus.curabitur@aol.couk','302-762-63-23','https://ebay.com/en-ca',2,'2024-02-26 13:30:10'),(30,'Cynthia','Barker','JMT92GXM9CL','donec.tempor@aol.org','302-549-25-67','https://whatsapp.com/sub',2,'2024-02-26 13:30:10'),(31,'Delilah','Wilkins','IGF68XPT4MK','et.libero@icloud.couk','302-348-78-44','http://netflix.com/settings',2,'2024-02-26 13:30:10'),(32,'Samantha','Morin','CPE29MSH7KH','est.congue.a@icloud.ca','302-384-48-15','http://ebay.com/site',2,'2024-02-26 13:30:10'),(33,'Susan','Vance','GQJ87LUA4IK','ultrices@aol.com','302-934-26-56','https://facebook.com/group/9',2,'2024-02-26 13:30:10'),(34,'Barclay','Waters','MYW24XQN3DT','curabitur.egestas.nunc@outlook.com','302-176-13-29','https://zoom.us/fr',2,'2024-02-26 13:30:10'),(35,'Indigo','Dickson','MCJ91UEB1MG','lacus.cras@outlook.couk','302-565-62-34','https://zoom.us/one',2,'2024-02-26 13:30:10'),(36,'Brody','Mclean','LDY85LOY4JH','eleifend.nunc@hotmail.edu','302-233-74-52','http://twitter.com/en-us',2,'2024-02-26 13:30:10');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios_met_pago`
--

DROP TABLE IF EXISTS `usuarios_met_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_met_pago` (
  `usuario_met_pago_id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `met_pago_id` int NOT NULL,
  PRIMARY KEY (`usuario_met_pago_id`),
  KEY `fk_usuarios_met_pago_usuarios_idx` (`usuario_id`),
  KEY `fk_usuarios_met_pago_metodos_pago_idx` (`met_pago_id`),
  CONSTRAINT `fk_usuarios_met_pago_metodos_pago` FOREIGN KEY (`met_pago_id`) REFERENCES `metodos_pago` (`met_pago_id`),
  CONSTRAINT `fk_usuarios_met_pago_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios_met_pago`
--

LOCK TABLES `usuarios_met_pago` WRITE;
/*!40000 ALTER TABLE `usuarios_met_pago` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuarios_met_pago` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-03-09 11:27:58
