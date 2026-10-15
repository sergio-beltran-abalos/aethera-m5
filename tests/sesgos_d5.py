"""
Diagnóstico: ¿las etiquetas de motivo de D5 informan algo sobre el texto?
"""
from aethera import datos

d5 = datos.cargar()["D5"]

# 1 · ¿Un mismo mensaje inicial aparece con motivos distintos?
primeras = d5["texto_inicial"].str.strip()
grupos = primeras.groupby(primeras).nunique()
print(f"Mensajes iniciales únicos           : {grupos.size:,}")
print(f"  con UN solo motivo                 : {(grupos == 1).sum():,} "
      f"({(grupos == 1).mean():.1%})")
print(f"  con 2 o más motivos distintos      : {(grupos > 1).sum():,} "
      f"({(grupos > 1).mean():.1%})")
print(f"  motivos distintos por mensaje      : media {grupos.mean():.2f}, máx {grupos.max()}")

# 2 · ¿La longitud del texto predice el motivo?
d5 = d5.assign(largo=primeras.str.len())
print("\nLargo medio del mensaje por motivo:")
print(d5.groupby("motivo")["largo"].agg(["mean", "std", "count"]).round(1))

# 3 · Un clasificador de texto puede predecir el motivo?
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

X = TfidfVectorizer().fit_transform(primeras)
y = d5["motivo"]
acc = cross_val_score(LogisticRegression(max_iter=2000), X, y, cv=5).mean()
mayor = y.value_counts(normalize=True).max()
azar = sum(p ** 2 for p in y.value_counts(normalize=True))
print(f"\nClasificador TF-IDF → motivo         : {acc:.1%}")
print(f"Clase mayoritaria                    : {mayor:.1%}")
print(f"Predicción por frecuencia            : {azar:.1%}")
print(f"A lift sobre la línea base          : {acc - mayor:+.1%}")

# 4 · ¿La derivación de D5 depende del motivo?
coh = (d5["tipo_derivado"] == d5["tipo_esperado"]).mean()
print(f"\nDerivación D5 vs. mapa de D2        : {coh:.1%}  (azar ≈ 33%)")
print("Cruce motivo × tipo derivado:")
print(pd.crosstab(d5["motivo"], d5["tipo_derivado"]))
