# services/dataset_generate.py
import logging
import asyncio
import pandas as pd

from services.bibit import get_all_bibit
from services.kolam import get_all_kolam, get_kolam_status
from services.pakan_stok import get_all_pakan_stok
from services.kematian import get_all_kematian
from services.panen import get_all_panen
from lib.supabase_client import get_db

logger = logging.getLogger("service_dataset")
logging.basicConfig(level=logging.INFO)


# ======================================================
# Ambil semua user_id unik dari Kolam
# ======================================================
async def get_all_user_ids():
    db = get_db()

    def db_call():
        return db.table("Kolam").select("user_id").execute()

    res = await asyncio.to_thread(db_call)

    if not res.data:
        logger.warning("Tidak ada user_id di Kolam")
        return []

    return list({row["user_id"] for row in res.data})


# ======================================================
# Dataset semua user
# ======================================================
async def generate_dataset_all_users(output_file: str = "dataset_panen.csv"):
    user_ids = await get_all_user_ids()
    if not user_ids:
        return None

    dfs = []
    for user_id in user_ids:
        df = await generate_dataset(user_id)
        if df is not None and not df.empty:
            dfs.append(df)

    if not dfs:
        logger.warning("Dataset kosong")
        return None

    df_all = pd.concat(dfs, ignore_index=True)
    df_all.to_csv(output_file, index=False)
    logger.info(f"Dataset ML dibuat: {output_file}")

    return df_all


# ======================================================
# Dataset per user (100% sesuai skema DB)
# ======================================================
async def generate_dataset(user_id: int):
    try:
        logger.info(f"Generate dataset user_id={user_id}")

        kolam = await get_all_kolam(user_id)
        if not kolam:
            return None

        bibit = await get_all_bibit(user_id)
        pakan = await get_all_pakan_stok(user_id)
        kematian = await get_all_kematian(user_id)
        panen = await get_all_panen(user_id)

        # =========================
        # KOLAM (BASE)
        # =========================
        df = pd.DataFrame(kolam)

        # PK pasti "id" sesuai DDL
        kolam_pk = "id"

        # Status panen
        df["status_panen"] = df.apply(get_kolam_status, axis=1)

        # =========================
        # BIBIT
        # =========================
        if bibit:
            df_bibit = (
                pd.DataFrame(bibit)
                .groupby("kolam_id")
                .agg(
                    total_bibit=("jumlah", "sum"),
                    total_berat_bibit=("total_berat", "sum"),
                    total_biaya_bibit=("total_harga", "sum"),
                )
                .reset_index()
            )

            df = df.merge(
                df_bibit,
                left_on=kolam_pk,
                right_on="kolam_id",
                how="left",
            ).drop(columns=["kolam_id"], errors="ignore")

        # =========================
        # PAKAN (PakanStok.jumlah)
        # =========================
        if pakan:
            df_pakan = (
                pd.DataFrame(pakan)
                .groupby("kolam_id")
                .agg(
                    total_pakan=("jumlah", "sum"),
                    total_biaya_pakan=("harga", "sum"),
                )
                .reset_index()
            )

            df = df.merge(
                df_pakan,
                left_on=kolam_pk,
                right_on="kolam_id",
                how="left",
            ).drop(columns=["kolam_id"], errors="ignore")

        # =========================
        # KEMATIAN
        # =========================
        if kematian:
            df_mati = (
                pd.DataFrame(kematian)
                .groupby("kolam_id")["jumlah"]
                .sum()
                .reset_index()
                .rename(columns={"jumlah": "total_kematian"})
            )

            df = df.merge(
                df_mati,
                left_on=kolam_pk,
                right_on="kolam_id",
                how="left",
            ).drop(columns=["kolam_id"], errors="ignore")

        # =========================
        # PANEN
        # =========================
        if panen:
            df_panen = (
                pd.DataFrame(panen)
                .groupby("kolam_id")
                .agg(
                    berat_panen=("total_berat", "sum"),
                    total_jual=("total_jual", "sum"),
                )
                .reset_index()
            )

            df = df.merge(
                df_panen,
                left_on=kolam_pk,
                right_on="kolam_id",
                how="left",
            ).drop(columns=["kolam_id"], errors="ignore")

        # =========================
        # NORMALISASI
        # =========================
        for col in [
            "total_bibit",
            "total_berat_bibit",
            "total_biaya_bibit",
            "total_pakan",
            "total_biaya_pakan",
            "total_kematian",
            "berat_panen",
            "total_jual",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # =========================
        # FCR
        # =========================
        df["fcr"] = df.apply(
            lambda x: (
                x["total_pakan"] / x["berat_panen"] if x["berat_panen"] > 0 else 0
            ),
            axis=1,
        )

        # =========================
        # META
        # =========================
        df["user_id"] = user_id

        logger.info(f"Dataset user_id={user_id} OK ({len(df)} baris)")
        return df

    except Exception:
        logger.exception(f"Gagal generate dataset user_id={user_id}")
        return None


if __name__ == "__main__":
    asyncio.run(generate_dataset_all_users())
