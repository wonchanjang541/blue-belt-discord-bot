import os
import io
import random
import sqlite3
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "blue_belt_base.png"
DB_PATH = BASE_DIR / "enhance.db"

# ===== 푸른 복대 정옵 =====
BASE_MAIN = 10
BASE_ATK = 2
BASE_MATK = 2
BASE_MDEF = 50
BASE_SLOTS = 3

# 혼돈의 주문서 60%
SUCCESS_RATE = 0.60
DELTA_MIN = -5
DELTA_MAX = 5

# False로 바꾸면 스탯이 음수까지 내려갈 수 있습니다.
# 게임 느낌상 음수 능력치는 어색해서 기본값은 0에서 멈추게 해뒀습니다.
CLAMP_STATS_AT_ZERO = True

def get_font(size: int):
    candidates = [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\malgunbd.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

FONT_16 = get_font(16)
FONT_17 = get_font(17)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            user_id INTEGER PRIMARY KEY,
            main_stat INTEGER NOT NULL,
            atk INTEGER NOT NULL,
            matk INTEGER NOT NULL,
            mdef INTEGER NOT NULL,
            slots INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            successes INTEGER NOT NULL DEFAULT 0
        )
        """)
        conn.commit()

def ensure_user(user_id: int):
    with db() as conn:
        conn.execute("""
        INSERT OR IGNORE INTO items
        (user_id, main_stat, atk, matk, mdef, slots, attempts, successes)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """, (user_id, BASE_MAIN, BASE_ATK, BASE_MATK, BASE_MDEF, BASE_SLOTS))
        conn.commit()

def get_item(user_id: int):
    ensure_user(user_id)
    with db() as conn:
        return conn.execute("SELECT * FROM items WHERE user_id = ?", (user_id,)).fetchone()

def reset_item(user_id: int):
    with db() as conn:
        conn.execute("""
        INSERT INTO items (user_id, main_stat, atk, matk, mdef, slots, attempts, successes)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        ON CONFLICT(user_id) DO UPDATE SET
            main_stat=excluded.main_stat,
            atk=excluded.atk,
            matk=excluded.matk,
            mdef=excluded.mdef,
            slots=excluded.slots,
            attempts=0,
            successes=0
        """, (user_id, BASE_MAIN, BASE_ATK, BASE_MATK, BASE_MDEF, BASE_SLOTS))
        conn.commit()

def clamp(v: int) -> int:
    return max(0, v) if CLAMP_STATS_AT_ZERO else v

def use_chaos_scroll(user_id: int):
    item = get_item(user_id)
    if item["slots"] <= 0:
        return {"ok": False, "reason": "업그레이드 가능 횟수가 0입니다."}

    success = random.random() < SUCCESS_RATE
    deltas = {"main_stat": 0, "atk": 0, "matk": 0, "mdef": 0}

    new_main = item["main_stat"]
    new_atk = item["atk"]
    new_matk = item["matk"]
    new_mdef = item["mdef"]

    if success:
        # 각 능력치가 서로 독립적으로 -5 ~ +5
        deltas = {
            "main_stat": random.randint(DELTA_MIN, DELTA_MAX),
            "atk": random.randint(DELTA_MIN, DELTA_MAX),
            "matk": random.randint(DELTA_MIN, DELTA_MAX),
            "mdef": random.randint(DELTA_MIN, DELTA_MAX),
        }
        new_main = clamp(new_main + deltas["main_stat"])
        new_atk = clamp(new_atk + deltas["atk"])
        new_matk = clamp(new_matk + deltas["matk"])
        new_mdef = clamp(new_mdef + deltas["mdef"])

    new_slots = item["slots"] - 1

    with db() as conn:
        conn.execute("""
        UPDATE items
        SET main_stat=?, atk=?, matk=?, mdef=?, slots=?,
            attempts=attempts+1,
            successes=successes+?
        WHERE user_id=?
        """, (
            new_main, new_atk, new_matk, new_mdef, new_slots,
            1 if success else 0,
            user_id
        ))
        conn.commit()

    return {
        "ok": True,
        "success": success,
        "deltas": deltas,
        "before": dict(item),
        "after": dict(get_item(user_id))
    }

def fmt_stat(label: str, current: int, base: int) -> str:
    diff = current - base
    if diff == 0:
        return f"{label} : +{current}"
    sign = "+" if diff > 0 else "-"
    return f"{label} : +{current} ({base}{sign}{abs(diff)})"

def draw_centered(draw, xy, text, font, fill=(240, 240, 255, 255)):
    draw.text(
        xy, text, font=font, fill=fill,
        anchor="mm",
        stroke_width=1,
        stroke_fill=(30, 30, 70, 255)
    )

def render_item_png(item) -> io.BytesIO:
    img = Image.open(IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # 원본의 능력치 부분을 덮고 새 수치를 그립니다.
    # 이미지가 315x385 기준일 때 맞춘 좌표입니다.
    draw.rectangle((8, 265, 306, 383), fill=(28, 28, 72, 238))

    # 가로 구분선
    for y in [287, 310, 333, 356, 380]:
        draw.line((8, y, 306, y), fill=(125, 130, 190, 165), width=1)

    lines = [
        fmt_stat("주스텟", item["main_stat"], BASE_MAIN),
        fmt_stat("공격력", item["atk"], BASE_ATK),
        fmt_stat("마력", item["matk"], BASE_MATK),
        fmt_stat("마법방어력", item["mdef"], BASE_MDEF),
        f"업그레이드 가능횟수 : {item['slots']}",
    ]
    ys = [276, 299, 322, 345, 369]

    for text, y in zip(lines, ys):
        draw_centered(draw, (157, y), text, FONT_16)

    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return out

def item_embed(user: discord.abc.User, item, result=None):
    embed = discord.Embed(
        title="푸른 복대 - 혼돈의 주문서 시뮬레이터",
        description=f"{user.mention}님의 푸른 복대",
        color=0x5865F2
    )

    if result and result.get("ok"):
        if result["success"]:
            d = result["deltas"]
            def ds(v): return f"+{v}" if v >= 0 else str(v)
            embed.add_field(
                name="📜 혼돈의 주문서 60% 성공!",
                value=(
                    f"주스텟 {ds(d['main_stat'])} / "
                    f"공격력 {ds(d['atk'])}\n"
                    f"마력 {ds(d['matk'])} / "
                    f"마법방어력 {ds(d['mdef'])}"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="💥 주문서 실패",
                value="능력치는 그대로이며 업그레이드 가능 횟수만 1 감소했습니다.",
                inline=False
            )

    embed.add_field(
        name="현재 능력치",
        value=(
            f"주스텟 **{item['main_stat']}**\n"
            f"공격력 **{item['atk']}** / 마력 **{item['matk']}**\n"
            f"마법방어력 **{item['mdef']}**\n"
            f"남은 업횟 **{item['slots']}**"
        ),
        inline=False
    )
    embed.set_image(url="attachment://blue_belt.png")
    embed.set_footer(text=f"성공률 60% · 성공 시 각 스탯 독립 -5~+5 · 시도 {item['attempts']}회")
    return embed

class EnhanceView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=600)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "이 강화창은 만든 사람만 사용할 수 있어요. `/강화`로 본인 장비를 열어주세요.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="혼줌 60% 사용", style=discord.ButtonStyle.primary, emoji="📜")
    async def chaos(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = use_chaos_scroll(interaction.user.id)
        item = get_item(interaction.user.id)

        if not result["ok"]:
            await interaction.response.send_message(result["reason"], ephemeral=True)
            return

        image = render_item_png(item)
        file = discord.File(image, filename="blue_belt.png")
        embed = item_embed(interaction.user, item, result=result)

        if item["slots"] <= 0:
            button.disabled = True

        await interaction.response.edit_message(
            embed=embed,
            attachments=[file],
            view=self
        )

    @discord.ui.button(label="내 장비 보기", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def view_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        item = get_item(interaction.user.id)
        image = render_item_png(item)
        file = discord.File(image, filename="blue_belt.png")
        await interaction.response.edit_message(
            embed=item_embed(interaction.user, item),
            attachments=[file],
            view=self
        )

    @discord.ui.button(label="초기화", style=discord.ButtonStyle.danger, emoji="🔄")
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        reset_item(interaction.user.id)
        item = get_item(interaction.user.id)
        image = render_item_png(item)
        file = discord.File(image, filename="blue_belt.png")

        # 초기화 뒤 강화 버튼 다시 활성화
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "혼줌 60% 사용":
                child.disabled = False

        embed = item_embed(interaction.user, item)
        embed.add_field(name="🔄 초기화 완료", value="정옵 푸른 복대로 되돌렸습니다.", inline=False)
        await interaction.response.edit_message(
            embed=embed,
            attachments=[file],
            view=self
        )

class EnhanceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        init_db()
        await self.tree.sync()

bot = EnhanceBot()

@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user} ({bot.user.id})")
    print("슬래시 명령어 동기화 완료")

@bot.tree.command(name="강화", description="푸른 복대 혼돈의 주문서 60% 시뮬레이터를 엽니다.")
async def enhance(interaction: discord.Interaction):
    item = get_item(interaction.user.id)
    image = render_item_png(item)
    file = discord.File(image, filename="blue_belt.png")
    view = EnhanceView(interaction.user.id)

    if item["slots"] <= 0:
        for child in view.children:
            if isinstance(child, discord.ui.Button) and child.label == "혼줌 60% 사용":
                child.disabled = True

    await interaction.response.send_message(
        embed=item_embed(interaction.user, item),
        file=file,
        view=view
    )

@bot.tree.command(name="내장비", description="현재 푸른 복대 상태를 봅니다.")
async def my_item(interaction: discord.Interaction):
    item = get_item(interaction.user.id)
    image = render_item_png(item)
    file = discord.File(image, filename="blue_belt.png")
    await interaction.response.send_message(
        embed=item_embed(interaction.user, item),
        file=file,
        ephemeral=True
    )

@bot.tree.command(name="강화초기화", description="내 푸른 복대를 정옵 상태로 초기화합니다.")
async def reset_cmd(interaction: discord.Interaction):
    reset_item(interaction.user.id)
    item = get_item(interaction.user.id)
    image = render_item_png(item)
    file = discord.File(image, filename="blue_belt.png")
    embed = item_embed(interaction.user, item)
    embed.add_field(name="🔄 초기화 완료", value="정옵 상태로 되돌렸습니다.", inline=False)
    await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

@bot.tree.command(name="강화랭킹", description="공격력 기준 푸른 복대 강화 랭킹을 봅니다.")
async def ranking(interaction: discord.Interaction):
    with db() as conn:
        rows = conn.execute("""
            SELECT user_id, main_stat, atk, matk, mdef, slots
            FROM items
            ORDER BY atk DESC, main_stat DESC, matk DESC
            LIMIT 10
        """).fetchall()

    if not rows:
        await interaction.response.send_message("아직 강화 기록이 없습니다.", ephemeral=True)
        return

    lines = []
    for i, r in enumerate(rows, 1):
        user = bot.get_user(r["user_id"])
        name = user.display_name if user else f"유저 {r['user_id']}"
        lines.append(
            f"**{i}. {name}** — 공 {r['atk']} / 주 {r['main_stat']} / 마 {r['matk']} / 마방 {r['mdef']}"
        )

    embed = discord.Embed(title="🏆 푸른 복대 강화 랭킹", description="\n".join(lines), color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN 환경변수가 없습니다. "
        "Windows PowerShell 예: $env:DISCORD_BOT_TOKEN='봇토큰'"
    )

bot.run(token)
