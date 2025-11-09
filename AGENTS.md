# AGENTS.md

## 0) Propósito

Este documento define **cómo debe trabajar un agente** (IA/coder) en este proyecto:

* Qué puede y no puede cambiar.
* Estándares de  **estilo, testing, logs y comentarios** .
* **Comandos de entorno** (instalación, ejecución, tests).
* **Reglas de seguridad** (secretos, datos).
* **Criterios de calidad** y checklist antes de abrir un PR.

## 1) Stack y alcance

* **Lenguaje** : Siempre **Python** (3.10.11). No usar otros lenguajes.
* **Trading** : Base preferente  **Pandas** . Pandas/Numpy para data pipes.
* **Paradigma** : Priorizar  **Programación Orientada a Objetos (POO)** , clases limpias y módulos ordenados.
* **Metodologia** : TDD (Test-Driven Development) o Desarrollo Guiado por Pruebas.
* **Estilo** :  **Código minimalista y autoexplicativo** . Donde no sea autoexplicativo, añadir **comentarios extensos** tras cada función/bloque.
* **Logging** : Incluir **muchos logs** (nivel DEBUG/INFO) a lo largo del flujo para trazar cada paso. Se podrán desactivar más tarde.
* **Formato** : **No usar emoticonos** en el código ni en mensajes de log.

## 2) Principios de edición (muy importante)

1. **Respeta el código estable** : Si el usuario indica que ciertos bloques  **no deben modificarse** ,  **no los toques** . Si es imprescindible, propón cambios aislados y justificados.
2. **Cambios mínimos** : Prefiere refactorizaciones **incrementales** y atómicas.
3. **Retrocompatibilidad** : No rompas interfaces públicas (nombres de clases/métodos/funciones) sin migración clara.
4. **Explica lo no obvio** : Si introduces lógica compleja, añade comentarios extensos al final del bloque/función.
5. **Logs primero** : Todo nuevo flujo debe traer logs suficientemente detallados de entrada, salida y decisiones.

## 3) Reglas de decisión del agente

1. Si hay **AGENTS.md** en la subcarpeta actual, úsalo con **prioridad** sobre el de la raíz.
2. Si el usuario da una instrucción explícita,  **esa instrucción manda** .
3. En caso de conflicto entre estilo y funcionalidad, **mantén la funcionalidad** y documenta el compromiso.

## 4) Mantenimiento

* Este archivo es  **vivo** : actualízalo cuando cambien convenciones o tooling.
* Añade ejemplos concretos de comando/estructura según el proyecto.
* Revisa que las secciones reflejen  **cómo trabajas realmente** .


