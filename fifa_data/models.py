"""
SoFIFA Django Models — corrigido com base na API oficial SoFIFA.

Fontes de referência:
  - GET /leagues, /league/{id}/{roster}
  - GET /teams/{roster}, /team/{id}
  - GET /player/{id}, /player/{id}/{roster}, /player/{id}/prime
  - GET /traits, /playStyles, /playStylesPlus, /specialities
  - GET /playerRole, /accelerationType

Convenções:
  - Todos os campos em snake_case (conversão do camelCase da API)
  - trait1/trait2 são bitmasks (BigIntegerField), não FKs
  - birth_date é offset de dias desde data base FIFA (IntegerField)
  - Relações M2M modeladas com tabelas intermediárias explícitas
"""

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# ============================================================
# LOOKUP TABLES (listas retornadas por endpoints de metadados)
# ============================================================

class Gender(models.Model):
    """
    Valores: 'male' | 'female'
    Origem: campo 'gender' em leagues, teams e players.
    """
    MALE = "male"
    FEMALE = "female"
    CHOICES = [(MALE, "Male"), (FEMALE, "Female")]

    name = models.CharField(max_length=10, unique=True, choices=CHOICES)

    class Meta:
        db_table = "genders"

    def __str__(self):
        return self.name


class Country(models.Model):
    """
    Países retornados nos objetos de liga, clube e jogador.
    Ex: 'Denmark', 'England', 'Brazil'
    """
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "countries"

    def __str__(self):
        return self.name


class LeagueType(models.Model):
    """
    Tipos de liga retornados pela API: 'domestic' | 'international' | 'cup' | 'friendly' | 'national'
    """
    CHOICES = [
        ("domestic", "Doméstica"),
        ("international", "Internacional"),
        ("cup", "Copa"),
        ("friendly", "Amistoso"),
        ("national", "Seleção"),
    ]
    name = models.CharField(max_length=50, unique=True, choices=CHOICES)

    class Meta:
        db_table = "league_types"

    def __str__(self):
        return self.name


class AccelerationType(models.Model):
    """
    GET /accelerationType/{version}
    Ex: 'Explosive', 'Controlled', 'Mostly Explosive', 'Mostly Controlled', 'Balanced'
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "acceleration_types"

    def __str__(self):
        return self.name


class TraitType(models.Model):
    """
    GET /traits/{version}
    Lista de traits indexada por posição de bit.
    Ex: 'Long throw-In', 'Power Free-Kick', ...

    IMPORTANTE: trait1 e trait2 nos jogadores são bitmasks (BigInt),
    não FKs diretas. Esta tabela serve para decodificar as máscaras:
    bit_position=0 → primeira trait da lista, etc.
    """
    name = models.CharField(max_length=255, unique=True)
    bit_position = models.IntegerField(
        unique=True,
        help_text="Posição do bit na bitmask de trait1/trait2",
    )
    version_introduced = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = "trait_types"
        ordering = ["bit_position"]

    def __str__(self):
        return self.name


class PlayStyle(models.Model):
    """
    GET /playStyles/{version}
    Ex: 'Finesse Shot', 'Technical', 'Flair', 'Quick Step'
    Disponível a partir da versão 24.
    """
    name = models.CharField(max_length=255, unique=True)
    version_introduced = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = "play_styles"

    def __str__(self):
        return self.name


class PlayStylePlus(models.Model):
    """
    GET /playStylesPlus/{version}
    Ex: 'Finesse Shot +', ...
    Versão aprimorada dos PlayStyles.
    """
    name = models.CharField(max_length=255, unique=True)
    version_introduced = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = "play_styles_plus"

    def __str__(self):
        return self.name


class Speciality(models.Model):
    """
    GET /specialities/{version}
    Ex: 'Speedster', 'Poacher', ...
    Retornado como lista de strings em player.specialities[].
    """
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "specialities"
        verbose_name_plural = "specialities"

    def __str__(self):
        return self.name


class FocusType(models.Model):
    """
    Focuses dentro de um PlayerRole.
    Ex: 'Defend', 'Balanced', 'Attack', 'Roaming'
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "focus_types"

    def __str__(self):
        return self.name


class Position(models.Model):
    """
    Tabela de referência para posições FIFA.
    Valores de 0 a 29 conforme documentação da API.

    0=GK, 1=SW, 2=RWB, 3=RB, 4=RCB, 5=CB, 6=LCB, 7=LB, 8=LWB,
    9=RDM, 10=CDM, 11=LDM, 12=RM, 13=RCM, 14=CM, 15=LCM, 16=LM,
    17=RAM, 18=CAM, 19=LAM, 20=RF, 21=CF, 22=LF, 23=RW, 24=RS,
    25=ST, 26=LS, 27=LW, 28=SUB, 29=RES
    """
    fifa_id = models.IntegerField(unique=True, help_text="Valor numérico retornado pela API")
    code = models.CharField(max_length=10, help_text="Ex: GK, CB, ST")
    name = models.CharField(max_length=100, help_text="Ex: Goalkeeper, Centre Back")

    class Meta:
        db_table = "positions"
        ordering = ["fifa_id"]

    def __str__(self):
        return f"{self.code} ({self.fifa_id})"


class PlayerRole(models.Model):
    """
    GET /playerRole/{version}
    Ex: {"name": "Winger +", "position": 23, "focuses": ["Balanced", "Attack"]}

    position aqui é o fifa_id da posição base do role.
    """
    name = models.CharField(max_length=255)
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player_roles",
        to_field="fifa_id",
        db_column="position_fifa_id",
    )
    focuses = models.ManyToManyField(
        FocusType,
        related_name="player_roles",
        blank=True,
    )

    class Meta:
        db_table = "player_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "position"], name="uq_player_role_name_position"
            )
        ]

    def __str__(self):
        return self.name


# ============================================================
# STADIUM
# ============================================================

class Stadium(models.Model):
    """
    Retornado via stadiumId no objeto de clube.
    """
    stadium_id = models.IntegerField(
        unique=True, help_text="ID oficial do jogo FIFA/FC"
    )
    name = models.CharField(max_length=255)
    capacity = models.IntegerField(null=True, blank=True)
    surface = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "stadiums"

    def __str__(self):
        return self.name


# ============================================================
# LEAGUE
# ============================================================

class League(models.Model):
    """
    GET /leagues, /league/{id}/{roster}

    Campos espelhados da API:
    {
      "id": 1, "name": "Superliga", "gender": "male",
      "country": "Denmark", "type": "domestic",
      "roster": "220001", "version": "22",
      "export": "160283", "latestRoster": "250016"
    }
    """
    fifa_id = models.IntegerField(
        unique=True, help_text="ID oficial do jogo FIFA/FC"
    )
    name = models.CharField(max_length=255)
    gender = models.ForeignKey(
        Gender, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leagues",
    )
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leagues",
    )
    league_type = models.ForeignKey(
        LeagueType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leagues",
    )
    roster = models.CharField(max_length=50, blank=True, null=True)
    version = models.CharField(max_length=10, blank=True, null=True)
    export = models.CharField(max_length=50, blank=True, null=True)
    latest_roster = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leagues"

    def __str__(self):
        return self.name


# ============================================================
# CLUB
# ============================================================

class Club(models.Model):
    """
    GET /teams/{roster}, /team/{id}

    Campos como xi_average_age são float na API (25.18).
    trait1 no clube também é bitmask (IntegerField).
    club_worth é inteiro (1871280) → BigIntegerField.
    rival_team_id é referência a outro Club (auto-referência).
    """
    fifa_id = models.IntegerField(
        unique=True, help_text="ID oficial do jogo FIFA/FC"
    )
    name = models.CharField(max_length=255)
    gender = models.ForeignKey(
        Gender, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clubs",
    )
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clubs",
    )
    club_type = models.ForeignKey(
        LeagueType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clubs",
    )
    league = models.ForeignKey(
        League, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clubs",
    )
    stadium = models.ForeignKey(
        Stadium, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clubs",
    )
    rival_club = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="rivals",
        help_text="rivalTeamId da API",
    )

    # Estatísticas do clube
    player_count = models.IntegerField(null=True, blank=True)
    transfer_budget = models.BigIntegerField(null=True, blank=True)
    int_prestige = models.IntegerField(null=True, blank=True)
    dom_prestige = models.IntegerField(null=True, blank=True)
    popularity = models.IntegerField(null=True, blank=True)
    youth_development = models.IntegerField(null=True, blank=True)
    club_worth = models.BigIntegerField(null=True, blank=True)
    opponent_weak_threshold = models.IntegerField(null=True, blank=True)
    opponent_strong_threshold = models.IntegerField(null=True, blank=True)

    # Idades médias — float conforme API (25.18)
    xi_average_age = models.FloatField(null=True, blank=True)
    total_average_age = models.FloatField(null=True, blank=True)

    # Ratings
    overall_rating = models.IntegerField(null=True, blank=True)
    attack_rating = models.IntegerField(null=True, blank=True)
    midfield_rating = models.IntegerField(null=True, blank=True)
    defense_rating = models.IntegerField(null=True, blank=True)

    # trait1 no clube é bitmask (ex: 180738)
    trait1 = models.BigIntegerField(null=True, blank=True)
    profitability = models.IntegerField(null=True, blank=True)

    # Build-up style
    bus_build_up_speed = models.IntegerField(null=True, blank=True)
    bus_passing = models.IntegerField(null=True, blank=True)
    bus_dribbling = models.IntegerField(null=True, blank=True)
    bus_positioning = models.IntegerField(null=True, blank=True)

    # Chance creation
    cc_crossing = models.IntegerField(null=True, blank=True)
    cc_passing = models.IntegerField(null=True, blank=True)
    cc_positioning = models.IntegerField(null=True, blank=True)
    cc_shooting = models.IntegerField(null=True, blank=True)

    # Defensive style
    def_aggression = models.IntegerField(null=True, blank=True)
    def_defender_line = models.IntegerField(null=True, blank=True)
    def_team_width = models.IntegerField(null=True, blank=True)
    def_mentality = models.IntegerField(null=True, blank=True)
    defensive_style = models.IntegerField(null=True, blank=True)
    defensive_width = models.IntegerField(null=True, blank=True)
    defensive_depth = models.IntegerField(null=True, blank=True)

    # Offensive style
    offensive_style = models.IntegerField(null=True, blank=True)
    offensive_width = models.IntegerField(null=True, blank=True)
    players_in_box_cross = models.IntegerField(null=True, blank=True)
    players_in_box_corner = models.IntegerField(null=True, blank=True)
    players_in_box_free_kick = models.IntegerField(null=True, blank=True)
    build_up_play = models.IntegerField(null=True, blank=True)
    chance_creation = models.IntegerField(null=True, blank=True)

    # Versioning
    roster = models.CharField(max_length=50, blank=True, null=True)
    version = models.CharField(max_length=10, blank=True, null=True)
    export = models.CharField(max_length=50, blank=True, null=True)
    latest_roster = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clubs"

    def __str__(self):
        return self.name


# ============================================================
# PLAYER
# ============================================================

class Player(models.Model):
    """
    Fonte: scraper sofifa.com (core/services/sofifa.py -> normalize.py -> ratings.py).

    Notas:
    - positions: lista de códigos de posição como string (ex: ["RB", "LB"]),
      não IDs numéricos — o sofifa não expõe posição como FK.
    - playstyles / roles: texto livre vindo do scraper, guardado como JSON.
      Podem evoluir para M2M via PlayStyle/PlayerRole no futuro, se
      quisermos normalizar por nome.
    - pac/sho/pas/dri/def_rating/phy: calculados em ratings.py a partir dos
      atributos brutos abaixo. None em goleiros.
    """

    fifa_id = models.IntegerField(unique=True, help_text="sofifa_id — ID do jogador no sofifa.com")
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    common_name = models.CharField(max_length=255, blank=True)

    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="players",
        help_text="Não preenchido pelo scraper atual — reservado para fonte futura",
    )
    gender = models.ForeignKey(
        Gender, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="players",
        help_text="Não preenchido pelo scraper atual — reservado para fonte futura",
    )
    acceleration_type = models.ForeignKey(
        AccelerationType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="players",
    )

    age = models.IntegerField(null=True, blank=True)

    # Físico
    height = models.IntegerField(null=True, blank=True, help_text="cm")
    weight = models.IntegerField(null=True, blank=True, help_text="kg")

    # Posições — texto livre, fiel ao que o sofifa entrega
    positions = models.JSONField(default=list, blank=True, help_text="Ex: ['RB', 'LB']")
    best_position = models.CharField(max_length=10, blank=True, null=True)

    # Pé e qualificações
    foot = models.IntegerField(null=True, blank=True, help_text="1=Right, 2=Left")
    weak_foot = models.IntegerField(null=True, blank=True, help_text="Estrelas 1-5")
    skill_moves = models.IntegerField(null=True, blank=True, help_text="Estrelas 1-5")
    international_reputation = models.IntegerField(null=True, blank=True, help_text="Estrelas 1-5")

    # Atributos técnicos
    crossing = models.IntegerField(null=True, blank=True)
    finishing = models.IntegerField(null=True, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    short_passing = models.IntegerField(null=True, blank=True)
    volleys = models.IntegerField(null=True, blank=True)
    dribbling = models.IntegerField(null=True, blank=True)
    curve = models.IntegerField(null=True, blank=True)
    free_kick = models.IntegerField(null=True, blank=True)
    long_passing = models.IntegerField(null=True, blank=True)
    ball_control = models.IntegerField(null=True, blank=True)

    # Físico / movimento
    acceleration = models.IntegerField(null=True, blank=True)
    sprint_speed = models.IntegerField(null=True, blank=True)
    agility = models.IntegerField(null=True, blank=True)
    reactions = models.IntegerField(null=True, blank=True)
    balance = models.IntegerField(null=True, blank=True)
    shot_power = models.IntegerField(null=True, blank=True)
    jumping = models.IntegerField(null=True, blank=True)
    stamina = models.IntegerField(null=True, blank=True)
    strength = models.IntegerField(null=True, blank=True)

    # Mentalidade / defesa
    long_shots = models.IntegerField(null=True, blank=True)
    aggression = models.IntegerField(null=True, blank=True)
    interceptions = models.IntegerField(null=True, blank=True)
    positioning = models.IntegerField(null=True, blank=True)
    vision = models.IntegerField(null=True, blank=True)
    penalties = models.IntegerField(null=True, blank=True)
    marking = models.IntegerField(null=True, blank=True, help_text="Defensive awareness")
    standing_tackle = models.IntegerField(null=True, blank=True)
    sliding_tackle = models.IntegerField(null=True, blank=True)
    composure = models.IntegerField(null=True, blank=True)

    # Goleiro
    gk_diving = models.IntegerField(null=True, blank=True)
    gk_handling = models.IntegerField(null=True, blank=True)
    gk_kicking = models.IntegerField(null=True, blank=True)
    gk_positioning = models.IntegerField(null=True, blank=True)
    gk_reflexes = models.IntegerField(null=True, blank=True)

    # Ratings gerais
    overall_rating = models.IntegerField(null=True, blank=True)
    potential = models.IntegerField(null=True, blank=True)

    # Finanças
    price = models.BigIntegerField(null=True, blank=True)
    wage = models.BigIntegerField(null=True, blank=True)

    # Ratings agregados (calculados em ratings.py)
    pac = models.IntegerField(null=True, blank=True)
    sho = models.IntegerField(null=True, blank=True)
    pas = models.IntegerField(null=True, blank=True)
    dri = models.IntegerField(null=True, blank=True)
    def_rating = models.IntegerField(
        null=True, blank=True, db_column="def_rating",
        help_text="Campo 'def' (renomeado para evitar conflito com keyword Python)",
    )
    phy = models.IntegerField(null=True, blank=True)

    # Texto livre vindo do scraper
    playstyles = models.JSONField(default=list, blank=True, help_text='Ex: ["Trivela", "Quick Step"]')
    player_roles = models.JSONField(
        default=list, blank=True,
        help_text='Ex: [{"role": "Wingback +", "position": "RB", "focuses": ["Balanced", "Support"]}]',
    )

    photo_url = models.URLField(max_length=500, blank=True, null=True)
    photo_base64 = models.TextField(
        blank=True, null=True,
        help_text=(
            "Foto do jogador já baixada e codificada como data URI base64 "
            "(ex: 'data:image/png;base64,...'). Evita depender do CDN externo "
            "do sofifa direto no <img src> do front (hotlink/CORS/expiração)."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "players"

    def __str__(self):
        return self.common_name or f"{self.first_name} {self.last_name}".strip()

    @property
    def positions_list(self) -> list[str]:
        """Mantido por compatibilidade com quem já usa essa property
        (ex: signal que cria o Product) — agora retorna os códigos direto."""
        return self.positions or []


class PlayerTeam(models.Model):
    """
    Relação entre jogador e clube, com contrato e posição no elenco.
    Espelha o array 'teams' retornado em GET /player/{id}.

    Exemplos de campos da API:
    {
      "id": 241, "name": "FC Barcelona", "position": 12,
      "jerseyNumber": 19, "joinTeamDate": 160602,
      "joinedYear": 2022, "joinedMonth": 7, "joinedDay": 1,
      "contractValidUntil": 2026, "teamIdLoanedFrom": 0, "loanDateEnd": 0
    }
    """
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="team_assignments"
    )
    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="player_assignments"
    )
    roster = models.CharField(
        max_length=50, help_text="Roster em que esta relação é válida"
    )

    # Posição no elenco (fifa_id de Position)
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        to_field="fifa_id",
        db_column="position_fifa_id",
        related_name="player_team_assignments",
    )
    jersey_number = models.IntegerField(null=True, blank=True)

    # Contrato
    join_team_date = models.IntegerField(
        null=True, blank=True, help_text="Offset de dias FIFA"
    )
    joined_year = models.IntegerField(null=True, blank=True)
    joined_month = models.IntegerField(null=True, blank=True)
    joined_day = models.IntegerField(null=True, blank=True)
    contract_valid_until = models.IntegerField(null=True, blank=True, help_text="Ano")

    # Empréstimo
    loaned_from_club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loans_out",
        help_text="teamIdLoanedFrom da API",
    )
    loan_date_end = models.IntegerField(
        null=True, blank=True, help_text="Offset de dias FIFA"
    )

    class Meta:
        db_table = "player_teams"
        constraints = [
            models.UniqueConstraint(
                fields=["player", "club", "roster"],
                name="uq_player_team_roster",
            )
        ]

    def __str__(self):
        return f"{self.player} @ {self.club} ({self.roster})"


# ============================================================
# M2M INTERMEDIÁRIAS
# ============================================================

class PlayerSpeciality(models.Model):
    """
    Relação player ↔ Speciality.
    Origem: player.specialities[] (lista de strings, ex: ["Speedster"])
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE)

    class Meta:
        db_table = "player_specialities"
        constraints = [
            models.UniqueConstraint(
                fields=["player", "speciality"], name="uq_player_speciality"
            )
        ]

    def __str__(self):
        return f"{self.player} — {self.speciality}"


class PlayerPlayStyle(models.Model):
    """
    Relação player ↔ PlayStyle.
    Origem: player.playStyle[] (lista de strings, ex: ["Finesse Shot", "Flair"])
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    play_style = models.ForeignKey(PlayStyle, on_delete=models.CASCADE)

    class Meta:
        db_table = "player_play_styles"
        constraints = [
            models.UniqueConstraint(
                fields=["player", "play_style"], name="uq_player_play_style"
            )
        ]

    def __str__(self):
        return f"{self.player} — {self.play_style}"


class PlayerPlayStylePlus(models.Model):
    """
    Relação player ↔ PlayStylePlus.
    Origem: player.playStylePlus[] (lista de strings, ex: ["Finesse Shot +"])
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    play_style_plus = models.ForeignKey(PlayStylePlus, on_delete=models.CASCADE)

    class Meta:
        db_table = "player_play_styles_plus"
        constraints = [
            models.UniqueConstraint(
                fields=["player", "play_style_plus"], name="uq_player_play_style_plus"
            )
        ]

    def __str__(self):
        return f"{self.player} — {self.play_style_plus}"


class PlayerRoleAssignment(models.Model):
    """
    Relação player ↔ PlayerRole por posição.
    Origem: player.role[] — cada item tem name, position, focuses[].

    Exemplo:
    {"name": "Winger +", "position": 23, "focuses": ["Balanced", "Attack"]}

    A posição aqui é a posição em que o jogador exerce aquele role
    (pode diferir da posição base do role em PlayerRole).
    """
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="role_assignments"
    )
    player_role = models.ForeignKey(
        PlayerRole, on_delete=models.CASCADE, related_name="assignments"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        to_field="fifa_id",
        db_column="position_fifa_id",
        related_name="role_assignments",
        help_text="Posição em que o jogador usa este role",
    )

    class Meta:
        db_table = "player_role_assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["player", "player_role", "position"],
                name="uq_player_role_position",
            )
        ]

    def __str__(self):
        return f"{self.player} — {self.player_role} @ {self.position}"


# ============================================================
# PLAYER PRIME (GET /player/{id}/prime)
# ============================================================

class PlayerPrime(models.Model):
    """
    GET /player/{id}/prime

    Armazena os valores máximos históricos de cada atributo do jogador
    e em qual roster cada pico foi atingido.
    """
    player = models.OneToOneField(
        Player, on_delete=models.CASCADE, related_name="prime"
    )

    # Cada atributo + roster em que foi máximo
    weak_foot = models.IntegerField(null=True, blank=True)
    weak_foot_roster = models.CharField(max_length=50, blank=True, null=True)
    crossing = models.IntegerField(null=True, blank=True)
    crossing_roster = models.CharField(max_length=50, blank=True, null=True)
    finishing = models.IntegerField(null=True, blank=True)
    finishing_roster = models.CharField(max_length=50, blank=True, null=True)
    heading = models.IntegerField(null=True, blank=True)
    heading_roster = models.CharField(max_length=50, blank=True, null=True)
    short_passing = models.IntegerField(null=True, blank=True)
    short_passing_roster = models.CharField(max_length=50, blank=True, null=True)
    volleys = models.IntegerField(null=True, blank=True)
    volleys_roster = models.CharField(max_length=50, blank=True, null=True)
    dribbling = models.IntegerField(null=True, blank=True)
    dribbling_roster = models.CharField(max_length=50, blank=True, null=True)
    curve = models.IntegerField(null=True, blank=True)
    curve_roster = models.CharField(max_length=50, blank=True, null=True)
    free_kick = models.IntegerField(null=True, blank=True)
    free_kick_roster = models.CharField(max_length=50, blank=True, null=True)
    long_passing = models.IntegerField(null=True, blank=True)
    long_passing_roster = models.CharField(max_length=50, blank=True, null=True)
    ball_control = models.IntegerField(null=True, blank=True)
    ball_control_roster = models.CharField(max_length=50, blank=True, null=True)
    acceleration = models.IntegerField(null=True, blank=True)
    acceleration_roster = models.CharField(max_length=50, blank=True, null=True)
    sprint_speed = models.IntegerField(null=True, blank=True)
    sprint_speed_roster = models.CharField(max_length=50, blank=True, null=True)
    agility = models.IntegerField(null=True, blank=True)
    agility_roster = models.CharField(max_length=50, blank=True, null=True)
    reactions = models.IntegerField(null=True, blank=True)
    reactions_roster = models.CharField(max_length=50, blank=True, null=True)
    balance = models.IntegerField(null=True, blank=True)
    balance_roster = models.CharField(max_length=50, blank=True, null=True)
    shot_power = models.IntegerField(null=True, blank=True)
    shot_power_roster = models.CharField(max_length=50, blank=True, null=True)
    jumping = models.IntegerField(null=True, blank=True)
    jumping_roster = models.CharField(max_length=50, blank=True, null=True)
    stamina = models.IntegerField(null=True, blank=True)
    stamina_roster = models.CharField(max_length=50, blank=True, null=True)
    strength = models.IntegerField(null=True, blank=True)
    strength_roster = models.CharField(max_length=50, blank=True, null=True)
    long_shots = models.IntegerField(null=True, blank=True)
    long_shots_roster = models.CharField(max_length=50, blank=True, null=True)
    aggression = models.IntegerField(null=True, blank=True)
    aggression_roster = models.CharField(max_length=50, blank=True, null=True)
    interceptions = models.IntegerField(null=True, blank=True)
    interceptions_roster = models.CharField(max_length=50, blank=True, null=True)
    positioning = models.IntegerField(null=True, blank=True)
    positioning_roster = models.CharField(max_length=50, blank=True, null=True)
    vision = models.IntegerField(null=True, blank=True)
    vision_roster = models.CharField(max_length=50, blank=True, null=True)
    penalties = models.IntegerField(null=True, blank=True)
    penalties_roster = models.CharField(max_length=50, blank=True, null=True)
    marking = models.IntegerField(null=True, blank=True)
    marking_roster = models.CharField(max_length=50, blank=True, null=True)
    standing_tackle = models.IntegerField(null=True, blank=True)
    standing_tackle_roster = models.CharField(max_length=50, blank=True, null=True)
    sliding_tackle = models.IntegerField(null=True, blank=True)
    sliding_tackle_roster = models.CharField(max_length=50, blank=True, null=True)
    gk_diving = models.IntegerField(null=True, blank=True)
    gk_diving_roster = models.CharField(max_length=50, blank=True, null=True)
    gk_handling = models.IntegerField(null=True, blank=True)
    gk_handling_roster = models.CharField(max_length=50, blank=True, null=True)
    gk_kicking = models.IntegerField(null=True, blank=True)
    gk_kicking_roster = models.CharField(max_length=50, blank=True, null=True)
    gk_positioning = models.IntegerField(null=True, blank=True)
    gk_positioning_roster = models.CharField(max_length=50, blank=True, null=True)
    gk_reflexes = models.IntegerField(null=True, blank=True)
    gk_reflexes_roster = models.CharField(max_length=50, blank=True, null=True)
    composure = models.IntegerField(null=True, blank=True)
    composure_roster = models.CharField(max_length=50, blank=True, null=True)
    overall_rating = models.IntegerField(null=True, blank=True)
    overall_rating_roster = models.CharField(max_length=50, blank=True, null=True)
    potential = models.IntegerField(null=True, blank=True)
    potential_roster = models.CharField(max_length=50, blank=True, null=True)
    growth = models.IntegerField(null=True, blank=True)
    growth_roster = models.CharField(max_length=50, blank=True, null=True)
    skill_moves = models.IntegerField(null=True, blank=True)
    skill_moves_roster = models.CharField(max_length=50, blank=True, null=True)

    # Totais agregados
    total_attacking = models.IntegerField(null=True, blank=True)
    total_attacking_roster = models.CharField(max_length=50, blank=True, null=True)
    total_skill = models.IntegerField(null=True, blank=True)
    total_skill_roster = models.CharField(max_length=50, blank=True, null=True)
    total_movement = models.IntegerField(null=True, blank=True)
    total_movement_roster = models.CharField(max_length=50, blank=True, null=True)
    total_power = models.IntegerField(null=True, blank=True)
    total_power_roster = models.CharField(max_length=50, blank=True, null=True)
    total_mentality = models.IntegerField(null=True, blank=True)
    total_mentality_roster = models.CharField(max_length=50, blank=True, null=True)
    total_defending = models.IntegerField(null=True, blank=True)
    total_defending_roster = models.CharField(max_length=50, blank=True, null=True)
    total_goalkeeping = models.IntegerField(null=True, blank=True)
    total_goalkeeping_roster = models.CharField(max_length=50, blank=True, null=True)
    total_overall = models.IntegerField(null=True, blank=True)
    total_overall_roster = models.CharField(max_length=50, blank=True, null=True)

    # PAC/SHO/PAS/DRI/DEF/PHY máximos
    pac = models.IntegerField(null=True, blank=True)
    pac_roster = models.CharField(max_length=50, blank=True, null=True)
    sho = models.IntegerField(null=True, blank=True)
    sho_roster = models.CharField(max_length=50, blank=True, null=True)
    pas = models.IntegerField(null=True, blank=True)
    pas_roster = models.CharField(max_length=50, blank=True, null=True)
    dri = models.IntegerField(null=True, blank=True)
    dri_roster = models.CharField(max_length=50, blank=True, null=True)
    def_rating = models.IntegerField(null=True, blank=True, db_column="def_rating")
    def_rating_roster = models.CharField(max_length=50, blank=True, null=True)
    phy = models.IntegerField(null=True, blank=True)
    phy_roster = models.CharField(max_length=50, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "player_prime"

    def __str__(self):
        return f"Prime of {self.player}"

@receiver(post_save, sender=Player)
def sync_product(sender, instance: Player, created, **kwargs):
    from products.models import Product
    Product.objects.update_or_create(
        player=instance,
        defaults={
            "title": instance.common_name or f"{instance.first_name} {instance.last_name}",
            "price": instance.price or 0,
            "category": instance.positions_list[0] if instance.positions_list else "",
            "quantity": 1,
        },
    )