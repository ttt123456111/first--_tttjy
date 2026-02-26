use rsa::{RsaPrivateKey, RsaPublicKey, Oaep};
use rsa::pkcs8::{EncodePrivateKey, EncodePublicKey, LineEnding};
use rand::rngs::OsRng;
use sha2::Sha256;
use mysql::*;
use mysql::prelude::*;
use std::fs;

// 定义数据结构
#[derive(Debug)]
struct EncryptedRecord {
    id: i32,
    original: String,
    encrypted_hex: String,
    decrypted: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🔐 RSA 加密测试程序");
    println!("===================");
    
    // 第一步：生成RSA密钥对
    println!("\n📝 1. 生成RSA密钥对...");
    let mut rng = OsRng;
    let bits = 2048;
    let private_key = RsaPrivateKey::new(&mut rng, bits)?;
    let public_key = RsaPublicKey::from(&private_key);
    println!("   ✅ 密钥对生成成功 ({} bits)", bits);
    
    // 第二步：原始消息
    let original_message = "HelloWorld from Rust RSA!";
    println!("\n📝 2. 原始消息: \"{}\"", original_message);
    println!("   消息长度: {} 字节", original_message.len());
    
    // 第三步：使用公钥加密
    println!("\n🔒 3. 使用公钥加密...");
    let padding = Oaep::new::<Sha256>();
    let encrypted_data = public_key.encrypt(&mut rng, padding, original_message.as_bytes())?;
    let encrypted_hex = hex::encode(&encrypted_data);
    println!("   加密后长度: {} 字节", encrypted_data.len());
    println!("   加密结果 (前50字符): {}...", &encrypted_hex[..50.min(encrypted_hex.len())]);
    
    // 第四步：使用私钥解密验证（这里需要重新创建 padding，因为上一步被 move 了）
    println!("\n🔓 4. 使用私钥解密验证...");
    let padding_for_decrypt = Oaep::new::<Sha256>();  // 重新创建 padding
    let decrypted_data = private_key.decrypt(padding_for_decrypt, &encrypted_data)?;
    let decrypted_message = String::from_utf8(decrypted_data)?;
    println!("   解密结果: \"{}\"", decrypted_message);
    
    // 验证一致性
    if original_message == decrypted_message {
        println!("   ✅ 加解密一致性验证通过");
    } else {
        println!("   ❌ 加解密验证失败");
    }
    
    // 第五步：保存密钥到文件
    println!("\n💾 5. 保存密钥到文件...");
    
    // 保存私钥 (PEM格式)
    let private_key_pem = private_key.to_pkcs8_pem(LineEnding::LF)?;
    fs::write("private_key.pem", private_key_pem.as_str())?;
    
    // 保存公钥 (PEM格式)
    let public_key_pem = public_key.to_public_key_pem(LineEnding::LF)?;
    fs::write("public_key.pem", public_key_pem.as_str())?;
    
    println!("   ✅ 私钥已保存: private_key.pem");
    println!("   ✅ 公钥已保存: public_key.pem");
    
    // 第六步：连接数据库保存结果
    println!("\n🗄️  6. 连接MySQL数据库...");
    
    // 数据库连接URL
    let db_url = "mysql://root:root123@localhost:3306/testdb";
    
    // 尝试连接数据库
    let pool = match Pool::new(db_url) {
        Ok(p) => {
            println!("   ✅ 数据库连接成功");
            p
        },
        Err(e) => {
            println!("   ❌ 数据库连接失败: {}", e);
            println!("   请确认MySQL容器是否运行: docker ps");
            return Ok(());
        }
    };
    
    let mut conn = pool.get_conn()?;
    
    // 创建表（如果不存在）
    conn.query_drop(
        r"CREATE TABLE IF NOT EXISTS rsa_test (
            id INT AUTO_INCREMENT PRIMARY KEY,
            original TEXT NOT NULL,
            encrypted TEXT NOT NULL,
            decrypted TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    )?;
    
    println!("   ✅ 表创建/验证成功");
    
    // 插入加密结果
    conn.exec_drop(
        r"INSERT INTO rsa_test (original, encrypted, decrypted) 
          VALUES (:original, :encrypted, :decrypted)",
        params! {
            "original" => original_message,
            "encrypted" => encrypted_hex,
            "decrypted" => decrypted_message,
        }
    )?;
    
    println!("   ✅ 数据插入成功");
    
    // 查询并显示最新记录
    let records: Vec<EncryptedRecord> = conn.query_map(
        "SELECT id, original, encrypted, decrypted FROM rsa_test ORDER BY id DESC LIMIT 1",
        |(id, original, encrypted_hex, decrypted)| {
            EncryptedRecord {
                id,
                original,
                encrypted_hex,
                decrypted,
            }
        }
    )?;
    
    if let Some(record) = records.first() {
        println!("\n📊 7. 数据库中的最新记录:");
        println!("   ID: {}", record.id);
        println!("   原始消息: {}", record.original);
        println!("   加密消息长度: {} 字节", record.encrypted_hex.len() / 2);
        println!("   解密消息: {}", record.decrypted);
        println!("   创建时间: 自动记录");
    }
    
    // 第八步：显示hello表的数据（验证原始需求）
    println!("\n📋 8. 验证 hello 表数据:");
    let hello_records: Vec<(i32, String)> = conn.query(
        "SELECT id, message FROM hello ORDER BY id"
    )?;
    
    for (id, message) in hello_records {
        println!("   ID: {}, 消息: \"{}\"", id, message);
    }
    
    println!("\n✅ 所有任务完成！");
    
    Ok(())
}
