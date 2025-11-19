import sqlite3

def check_current_violators():
    """Comparar sellers del email con violaciones actuales"""
    
    # Sellers del email a Daniel
    email_sellers = [
        "Dealsupply",
        "BBQ Authority Inc / Blazzing Fire", 
        "First Response Fireplace Products",
        "Jacks Small Engines",
        "myBBQdeals",
        "Electric Fireplaces Plus",
        "Electric Fireplaces Direct Outlet"
    ]
    
    conn = sqlite3.connect('violations_tracker.db')
    cursor = conn.cursor()
    
    print("=== ANÁLISIS DE SELLERS DEL EMAIL VS ESTADO ACTUAL ===\n")
    
    still_violating = []
    no_longer_violating = []
    
    for seller in email_sellers:
        # Verificar si aún tiene violaciones activas
        cursor.execute('''
            SELECT COUNT(*) as violations_count, 
                   MAX(days_active) as max_days,
                   pending_approval,
                   dns_added_date
            FROM violations 
            WHERE seller_name = ? AND status = "ACTIVE"
            GROUP BY pending_approval, dns_added_date
        ''', (seller,))
        
        result = cursor.fetchone()
        
        if result and result[0] > 0:  # Tiene violaciones activas
            violations_count, max_days, pending, dns_date = result
            
            # Obtener detalles de productos violando
            cursor.execute('''
                SELECT sku, product_description, current_price, map_price, days_active
                FROM violations 
                WHERE seller_name = ? AND status = "ACTIVE"
                ORDER BY days_active DESC
            ''', (seller,))
            
            products = cursor.fetchall()
            
            print(f"🔴 {seller}")
            print(f"   Status: {'EN DNS' if dns_date else 'PENDING APPROVAL' if pending else 'ACTIVO'}")
            print(f"   Total violaciones: {violations_count}")
            print(f"   Días máximos: {max_days}")
            print("   Productos violando:")
            
            for sku, desc, current_price, map_price, days in products:
                print(f"     - {desc} (SKU: {sku}) - ${current_price} (MAP: ${map_price}) - Day {days}")
            
            still_violating.append(seller)
            print()
            
        else:
            print(f"✅ {seller}")
            print("   Status: YA NO ESTÁ VIOLANDO (limpio)")
            no_longer_violating.append(seller)
            print()
    
    print("=" * 60)
    print(f"📊 RESUMEN:")
    print(f"   🔴 Aún violando: {len(still_violating)} sellers")
    print(f"   ✅ Ya no violan: {len(no_longer_violating)} sellers")
    
    if still_violating:
        print(f"\n🚨 SELLERS PARA SUBIR A DNS:")
        for seller in still_violating:
            print(f"   - {seller}")
    
    if no_longer_violating:
        print(f"\n✅ SELLERS QUE YA CORRIGIERON:")
        for seller in no_longer_violating:
            print(f"   - {seller}")
    
    conn.close()

if __name__ == "__main__":
    check_current_violators()