package deepdive.c01.l04;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/** stock 테이블을 읽는 보일러플레이트. 이 클래스는 손대지 않는다. */
final class StockTable {

    record Row(int qty, int version) {}

    private StockTable() {}

    /** @param forUpdate true 면 {@code SELECT … FOR UPDATE} · @return 행이 없으면 null */
    static Row read(Connection c, String sku, boolean forUpdate) throws SQLException {
        String sql = "SELECT qty, version FROM stock WHERE sku = ?" + (forUpdate ? " FOR UPDATE" : "");
        try (PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, sku);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? new Row(rs.getInt(1), rs.getInt(2)) : null;
            }
        }
    }
}
