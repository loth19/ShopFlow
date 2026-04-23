"""
FastAPI REST API pour ShopFlow
Endpoints: /products, /products/{id}, /stats/revenue, /stats/top-customers, /stats/top-products
"""

from fastapi import FastAPI, HTTPException
import sqlite3
import json
import os
import uvicorn
from typing import List, Dict, Any

app = FastAPI(
    title="ShopFlow API",
    version="1.0.0",
    description="API REST pour l'analyse des données ShopFlow"
)

# ==================== Utilitaires ====================

def get_db_path() -> str:
    """Détecte automatiquement le chemin vers la base de données SQLite."""
    paths = [
        "data/shopflow.db",
        "data/ShopFlow.db",
        "shopflow.db",
        "ShopFlow.db"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Base de données introuvable: data/shopflow.db ou data/ShopFlow.db")

DB_PATH = get_db_path()

def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Exécute une requête SQL et retourne tous les résultats en JSON."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur BD: {str(e)}")

def fetch_one(query: str, params: tuple = ()) -> Dict[str, Any] | None:
    """Exécute une requête SQL et retourne un seul résultat."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur BD: {str(e)}")

# ==================== Routes ====================

@app.get("/")
def read_root() -> Dict[str, Any]:
    """Endpoint racine avec documentation des endpoints disponibles."""
    return {
        "message": "ShopFlow API",
        "version": "1.0.0",
        "endpoints": {
            "/products": "GET - Tous les produits",
            "/products/{id}": "GET - Produit par ID",
            "/stats/revenue": "GET - Revenu total et panier moyen",
            "/stats/top-customers": "GET - Top clients par dépense (limit=10)",
            "/stats/top-products": "GET - Top produits par revenue (limit=10)"
        }
    }

@app.get("/products")
def get_products() -> List[Dict[str, Any]]:
    """Retourne tous les produits de la base de données."""
    query = "SELECT * FROM produit ORDER BY name ASC"
    return fetch_all(query)

@app.get("/products/{product_id}")
def get_product(product_id: int) -> Dict[str, Any]:
    """Retourne un produit spécifique par son ID."""
    query = "SELECT * FROM produit WHERE id = ?"
    result = fetch_one(query, (product_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result

@app.get("/stats/revenue")
def get_revenue_stats() -> Dict[str, Any]:
    """
    Retourne les statistiques de revenu:
    - nombre_commandes: nombre total de commandes complétées
    - revenue_total: revenu total en EUR
    - panier_moyen: panier moyen en EUR
    - revenue_par_mois: série mensuelle
    - revenue_par_categorie: répartition par catégorie
    """
    query_total = """
    SELECT 
        COUNT(*) as nombre_commandes,
        COALESCE(SUM(total_eur), 0.0) as revenue_total,
        COALESCE(AVG(total_eur), 0.0) as panier_moyen
    FROM commandes
    WHERE status = 'completed'
    """

    total_stats = fetch_one(query_total) or {
        "nombre_commandes": 0,
        "revenue_total": 0.0,
        "panier_moyen": 0.0,
    }
    total_stats["revenue_total"] = float(total_stats["revenue_total"] or 0.0)
    total_stats["panier_moyen"] = float(total_stats["panier_moyen"] or 0.0)

    query_month = """
    SELECT
        SUBSTR(date_commande, 1, 7) as mois,
        COALESCE(SUM(total_eur), 0.0) as revenue_eur
    FROM commandes
    WHERE status = 'completed'
    GROUP BY SUBSTR(date_commande, 1, 7)
    ORDER BY mois ASC
    """
    revenue_par_mois = fetch_all(query_month)
    for row in revenue_par_mois:
        row["revenue_eur"] = float(row["revenue_eur"] or 0.0)

    query_category = """
    SELECT
        p.category,
        COALESCE(SUM(co.total_eur), 0.0) as revenue_eur
    FROM commandes co
    INNER JOIN produit p ON co.produit_id = p.id
    WHERE co.status = 'completed'
    GROUP BY p.category
    ORDER BY revenue_eur DESC
    """
    revenue_par_categorie = fetch_all(query_category)
    for row in revenue_par_categorie:
        row["revenue_eur"] = float(row["revenue_eur"] or 0.0)

    return {
        "nombre_commandes": int(total_stats["nombre_commandes"] or 0),
        "revenue_total": total_stats["revenue_total"],
        "panier_moyen": total_stats["panier_moyen"],
        "revenue_par_mois": revenue_par_mois,
        "revenue_par_categorie": revenue_par_categorie,
    }

@app.get("/stats/top-customers")
def get_top_customers(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retourne les N clients avec la plus grande dépense totale.
    
    Parameters:
    - limit: nombre de clients à retourner (par défaut 10)
    
    Returns:
    List of clients with id, name, and total_spent in EUR
    """
    query = """
    SELECT 
        c.id,
        c.name as client_name,
        SUM(co.total_eur) as depense_totale_eur
    FROM client c
    INNER JOIN commandes co ON c.id = co.client_id
    WHERE co.status = 'completed'
    GROUP BY c.id, c.name
    ORDER BY depense_totale_eur DESC
    LIMIT ?
    """
    results = fetch_all(query, (limit,))
    for row in results:
        row["depense_totale_eur"] = float(row["depense_totale_eur"])
    return results

@app.get("/stats/top-products")
def get_top_products(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retourne les N produits avec le plus grand revenue.
    
    Parameters:
    - limit: nombre de produits à retourner (par défaut 10)
    
    Returns:
    List of products with id, name, category, and revenue in EUR
    """
    query = """
    SELECT 
        p.id,
        p.name,
        p.category,
        SUM(co.total_eur) as revenue_eur
    FROM produit p
    INNER JOIN commande_produit cp ON p.id = cp.produit_id
    INNER JOIN commandes co ON cp.commande_id = co.id
    WHERE co.status = 'completed'
    GROUP BY p.id, p.name, p.category
    ORDER BY revenue_eur DESC
    LIMIT ?
    """
    results = fetch_all(query, (limit,))
    for row in results:
        row["revenue_eur"] = float(row["revenue_eur"])
    return results

# ==================== Démarrage ====================

if __name__ == "__main__":
    uvicorn.run(
        "06_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
