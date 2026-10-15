"""Prueba de humo del núcleo: datos → segmentos → agenda → propuesta."""
import pandas as pd

from aethera import config as C, datos, horarios, servicios

pd.set_option("display.width", 250)

COLS = ["student_id", "district_id", "country_context", "study_mode",
        "employment_status", "work_hours_week", "services_awareness",
        "support_network", "academic_stage"]


def segmento():
    nova = datos.cargar()["D1"].query("institution_id == @C.INSTITUCION").copy()
    nova["f_desconoce"] = nova.services_awareness.eq("unaware")
    nova["f_sin_red"] = nova.support_network.isin(["limited", "none"])
    nova["f_nocturno"] = nova.study_mode.eq("evening")
    nova["n_fricciones"] = nova[["f_desconoce", "f_sin_red", "f_nocturno"]].sum(axis=1)
    mod = nova.anxiety_band.isin(["moderate", "high"])
    m5 = nova[mod & nova.previous_support_use.eq("never")]
    return nova, mod.sum(), m5, m5[m5.n_fricciones >= 2]


def perfil(seg, **cond):
    df = seg
    for k, v in cond.items():
        df = df[df[k] == v]
    fila = df.sort_values("student_id").iloc[0]
    return {c: (fila[c].item() if hasattr(fila[c], "item") else fila[c]) for c in COLS}


def main():
    nova, n_mod, m5, seg = segmento()
    print(f"NOVA {len(nova):,} | moderada/alta {n_mod:,} | M5 {len(m5):,} "
          f"({len(m5)/n_mod:.1%}) | prioritario {len(seg):,} ({len(seg)/len(m5):.1%} de M5)")
    print(f"M5 sobre moderada/alta global NOVA: {len(m5)/n_mod:.1%}\n")

    ag = servicios.Agenda()
    print("AGENDA:", ag.estadisticas(), "\n")

    casos = [
        ("A", dict(study_mode="day", employment_status="not_working", support_network="none")),
        ("B", dict(study_mode="evening", employment_status="full_time", support_network="limited")),
        ("C", dict(study_mode="evening", employment_status="part_time")),
    ]
    motivos = ["academic_pressure", "social_support", "career_concern",
               "sleep_and_routine", "preventive_guidance"]

    for nombre, cond in casos:
        p = perfil(seg, **cond)
        print(f"--- Perfil {nombre}: {p['student_id']} · {p['district_id']} · "
              f"{p['study_mode']}/{p['employment_status']} · {p['country_context']}")
        print(f"    horario   : {horarios.describir_horario(p)}")
        print(f"    carga D3  : {datos.d3_carga(p['student_id'])} créditos")
        print(f"    disponibles: {horarios.resumen_fronteras(p)}")
        for motivo in motivos:
            r = servicios.proponer_opciones(p, motivo, ag)
            ops = r["opciones"]
            dias = {o["fecha"] for o in ops}
            compatible = len(dias) == len(ops)
            print(f"    {motivo:20} {r['tipo_principal'][:22]:24} "
                  f"{len(ops)} ops | días distintos: {'sí' if compatible else 'NO ⚠'}")
            for o in ops:
                marca = " ⚠puente" if o["es_puente_pares"] else ""
                print(f"       {o['opcion']}. {o['dia']:9} {o['fecha']} {o['hora']} "
                      f"{o['servicio']:28} {o['canal']:11} "
                      f"P={o['p_asistencia']:.3f} conf={o['confianza_ml']}{marca}")
        print()


if __name__ == "__main__":
    main()
