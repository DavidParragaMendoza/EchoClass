# 📊 Rúbrica de Evaluación de Pronunciación (EchoClass)

Esta rúbrica establece la metodología objetiva para calificar la precisión de la pronunciación de un usuario al comparar el texto objetivo (la palabra o frase que debía decir) con la transcripción obtenida por la IA (**Whisper**).

---

## 📐 Algoritmo de Cálculo de Similitud

La puntuación se calcula utilizando la **Distancia de Levenshtein Normalizada** combinada con limpieza de texto (conversión a minúsculas, eliminación de signos de puntuación extra y normalización de espacios).

1. **Limpieza y Normalización**:
   $$\text{texto}_{\text{limpio}} = \text{normalizar}(\text{texto})$$
2. **Distancia de Edición ($D$)**: Número mínimo de inserciones, eliminaciones o sustituciones necesarias para transformar la transcripción en el texto objetivo.
3. **Porcentaje de Similitud ($S$)**:
   $$S = \left(1 - \frac{D}{\max(\text{longitud}(\text{objetivo}), \text{longitud}(\text{transcripción}))}\right) \times 100\%$$
4. **Conversión a Escala (1 a 10)**:
   $$\text{Nota} = \text{redondear}\left(\frac{S}{10}\right) \quad (\text{Mínimo: } 1, \text{ Máximo: } 10)$$

---

## 🏆 Escala de Calificación (1 a 10)

| Calificación | Rango de Similitud | Nivel | Descripción |
| :---: | :---: | :---: | :--- |
| **10 / 10** | **95% – 100%** | **Excelente** | Pronunciación perfecta o con variaciones imperceptibles. Whisper reconoció la palabra exacta. |
| **9 / 10** | **85% – 94%** | **Sobresaliente** | Pronunciación muy clara. Pequeña diferencia fonética o una letra sutil omitida. |
| **8 / 10** | **75% – 84%** | **Muy Bueno** | Comprensión alta. Ligera alteración en un fonema o terminación de palabra. |
| **7 / 10** | **65% – 74%** | **Bueno** | Comprensible, pero con acento o imprecisión en varias letras o sílabas. |
| **6 / 10** | **55% – 64%** | **Aceptable** | Se entiende la intención, pero la pronunciación requiere esfuerzo para ser reconocida. |
| **5 / 10** | **45% – 54%** | **Regular** | Aproximación básica. Se deformaron varias sílabas de la palabra objetivo. |
| **4 / 10** | **35% – 44%** | **Deficiente** | Pronunciación confusa. Solo se captó un fragmento débil o impreciso de la palabra. |
| **3 / 10** | **25% – 34%** | **Insuficiente** | Ruido significativo o pronunciación muy alejada de la palabra esperada. |
| **2 / 10** | **10% – 24%** | **Muy Bajo** | Prácticamente no se reconoce la palabra objetivo. Sonido distorsionado. |
| **1 / 10** | **0% – 9%** | **Sin Coincidencia** | El usuario no habló, dijo algo totalmente distinto o no hubo sonido inteligible. |

---

## 🌐 Notas de Precisión de Whisper según Idioma

Whisper es un modelo de reconocimiento de voz de alto rendimiento. Sin embargo, su precisión varía ligeramente según el idioma debido a la cantidad de datos de entrenamiento disponibles:

- 🇬🇧 **Inglés (`en`)** — **Excelente (~97%+)**: Es el idioma con mayor volumen de datos de entrenamiento en Whisper; reconoce acentos variados con máxima fidelidad.
- 🇪🇸 **Español (`es`)** — **Muy Alta (~95%+)**: Fonética clara y regular. Excelente desempeño en transcripción y pronunciación.
- 🇷🇺 **Ruso (`ru`)** — **Buena (~91% - 94%)**: Transcripción sólida en alfabeto cirílico con muy buena detección de vocales y consonantes.
- 🇨🇳 **Chino Mandarín (`zh`)** — **Alta (~88% - 92%)**: Alta precisión en palabras comunes; los tonos fonéticos complejos pueden requerir vocalizar claramente.
