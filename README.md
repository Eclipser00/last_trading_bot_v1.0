# last_trading_bot_v1.0
Trading bot.

Visión global (monolítico modular)
•	App (orquestador) → gobierna el ciclo de vida.
•	Config/Secrets → parámetros de ejecución y credenciales.
•	BrokerAdapter → capa única hacia MT5 (interfaz + implementación). (librería python metatrader5)
•	DataFeed + DataStore → ingesta y cache/ventanas de datos en DataFrames.
•	Strategy (Base + derivadas) → genera señales.
•	RiskManager → límites (DD cuenta 30%, DD por activo 30%, exposición global 80%, por activo configurable).
•	Portfolio → estado de posiciones, PnL, exposición.
•	OrderManager → traducción señal→orden, enrutado al MT5 (librería python metatrader5), seguimiento.
•	Scheduler/Clock/MarketHours → ritmo y ventanas operativas.
•	Logger/Audit/Metrics → trazabilidad, métricas y salud.
•	KillSwitch/HealthMonitor → seguridad y recuperación.
________________________________________
Clases principales
1) App
Rol: Punto de entrada; inicializa componentes y ejecuta el bucle principal.
•	Atributos
o	config: Config
o	secrets: SecretsManager
o	broker: BrokerAdapter
o	data_feed: DataFeed
o	data_store: DataStore
o	portfolio: Portfolio
o	risk: RiskManager
o	order_mgr: OrderManager
o	strategy_registry: StrategyRegistry
o	scheduler: Scheduler
o	market_hours: MarketHours
o	logger: Logger
o	audit: AuditTrail
o	metrics: Metrics
o	health: HealthMonitor
o	kill_switch: KillSwitch
•	Métodos
o	boot() → carga config/secretos, conecta broker, sanity checks.
o	run() → bucle: tick/cron → ingest → compute → risk → route orders → update state → log/metrics.
o	shutdown() → cierre ordenado, descarga estados.
o	reload_config() → permite cambiar toggles en caliente (si procede).
________________________________________
2) Config
Rol: Parámetros y toggles.
•	Atributos (ejemplos)
o	symbols: list[str]
o	timeframe: str (ej. “M1”, “M5”, “H1”)
o	max_account_drawdown: float (0.30)
o	max_symbol_drawdown: float (0.30)
o	max_account_exposure: float (0.80)
o	max_symbol_exposure: float (p.ej. 0.20–0.30)
o	risk_per_trade: float (ej. 0.01–0.02)
o	commissions, slippage, financing
o	market_schedule: dict (ventanas operativas)
o	storage_paths, log_level, heartbeat_ms
•	Métodos
o	validate() → reglas, rangos y consistencia.
o	from_file()/to_file().
________________________________________
3) SecretsManager
Rol: Custodia credenciales/API keys.
•	Atributos
o	store_path, encryption_key_ref
•	Métodos
o	get(key), set(key, value), rotate(key).
________________________________________
4) BrokerAdapter (interfaz)
Rol: Abstracción común para MT5/IB.
•	Métodos
o	connect()/disconnect()/is_connected()
o	Datos: get_quote(symbol), get_ohlc(symbol, timeframe, n), subscribe(symbols)
o	Cuenta: get_balance(), get_equity(), get_margin_used(), get_open_positions(), get_open_orders()
o	Órdenes: place_order(order: Order) → OrderID, modify_order(...), cancel_order(order_id), close_position(position_id, ...)
o	Eventos: on_fill(callback), on_order_update(callback), on_disconnect(callback)
Implementaciones: MT5Adapter(BrokerAdapter), IBAdapter(BrokerAdapter).
________________________________________
5) DataFeed (Extract_data)
Rol: Ingesta de datos en tiempo real/histórico desde BrokerAdapter.
•	Atributos
o	broker: BrokerAdapter, subscribed: set[str], buffer: dict[symbol → deque/timeseries]
•	Métodos
o	prime_history(symbols, timeframe, bars_back)
o	poll() → trae último tick/bar y lo envía a DataStore
o	resample_if_needed()
________________________________________
6) DataStore (Df_Creator)
Rol: Cache estructurada en pandas para estrategias.
•	Atributos
o	frames: dict[(symbol,timeframe) → pd.DataFrame]
o	features: dict[(symbol,timeframe) → dict[str → pd.Series]] (indicadores)
o	window_bars: int
•	Métodos
o	update_bar(symbol, timeframe, bar)
o	get_frame(symbol, timeframe) → DataFrame
o	compute_features(symbol, timeframe, feature_set) (Bollinger, RSI, MAs, etc.)
o	snapshot() → copia inmutable para estrategia.
________________________________________
7) StrategyBase (Market_logic)
Rol: Contrato para todas las estrategias.
•	Atributos
o	name: str, symbols: list[str], params: dict
o	state: dict (memoria interna por símbolo)
•	Métodos
o	on_bar(context: StrategyContext) → list[Signal]
o	on_fill(fill_event)
o	on_start()/on_stop()
o	health_check()
o	describe() → metadatos (inputs, outputs, riesgos típicos)
Derivadas: BollingerMeanRevert, TresMediasSlopeOnly, etc.
StrategyRegistry
•	Atributos: strategies: list[StrategyBase], enabled: set[str]
•	Métodos: register(), enable()/disable(), iterate().
StrategyContext
•	Atributos: data_store, portfolio_view, config, clock
•	Métodos: utilidades (posición actual, PnL por símbolo, volatilidad, etc.).
________________________________________
8) Signal
Rol: Intención de mercado generada por la estrategia.
•	Atributos
o	symbol, side (LONG/SHORT/CLOSE), strength, reason
o	entry_type (market/limit/stop), price_ref, ttl
o	stop_loss, take_profit (opcionales)
•	Métodos
o	is_valid(clock, market_hours)
________________________________________
9) RiskManager
Rol: Guardián de límites y sizing.
•	Atributos
o	config, portfolio, limits_state (DD cuenta/activo, exposiciones, pérdidas diarias)
•	Métodos
o	check_signal(signal) → RiskDecision (APROBAR/RECHAZAR/AJUSTAR)
o	position_sizing(signal) → size (por % riesgo y distancia a SL)
o	check_account_limits() → OK/Trigger (DD cuenta ≥ 30% ⇒ KillSwitch)
o	check_symbol_limits(symbol) → OK/Block (DD por activo ≥ 30%)
o	check_exposure_after(order) → OK/Reduce/Block (cuenta ≤ 80%; por activo ≤ X%)
o	register_fill(fill_event) (actualiza métricas de riesgo)
o	daily_reset() (reinicia contadores si procede)
________________________________________
10) Portfolio
Rol: Fuente de verdad de posiciones, PnL y exposición.
•	Atributos
o	positions: dict[symbol → Position]
o	orders: dict[id → Order]
o	cash, equity, margin_used, exposure_by_symbol
o	history: TradeLedger
•	Métodos
o	update_from_broker(broker_state)
o	get_exposure(symbol|total)
o	estimate_pnl(symbol)
o	apply_fill(fill_event)
o	close_all() (para KillSwitch)
Position
•	Atributos: symbol, side, size, avg_price, unrealized_pnl, stop_loss, take_profit, opened_at
•	Métodos: update_mtm(quote), set_sl/tp, risk_notional()
Order
•	Atributos: id, symbol, side, size, type, price, sl, tp, status, strategy_tag, created_at
•	Métodos: mark_working(), mark_filled(), mark_canceled()
________________________________________
11) OrderManager (Position_Creator)
Rol: Traduce señales aprobadas por riesgo en órdenes ejecutables.
•	Atributos
o	broker: BrokerAdapter, risk: RiskManager, portfolio: Portfolio
o	pending_queue: deque[Order]
•	Métodos
o	signal_to_order(signal) → Order (con sizing del RiskManager)
o	route(order) → broker.place_order(...)
o	amend(order_id, new_params)
o	cancel(order_id)
o	sync_with_broker() (reconcilia estados)
o	on_fill(fill_event) (impacta en Portfolio y Risk)
________________________________________
12) Scheduler / Clock / MarketHours
Rol: Ritmo, calendario y ventanas operativas.
•	Atributos
o	heartbeat_ms, sessions_by_symbol
•	Métodos
o	now(), sleep_until_next_beat()
o	is_open(symbol) (evita operar fuera de mercado)
o	next_session_open/close(symbol)
________________________________________
13) Logger / AuditTrail / Metrics
Rol: Observabilidad y trazabilidad.
•	Logger
o	info/debug/warn/error(evento estructurado)
•	AuditTrail
o	record_order(order), record_signal(signal), record_risk(decision), record_fill(fill)
•	Metrics
o	update_equity_curve(), update_drawdowns(), exposure_gauges()
o	export_snapshots() (CSV/DB)
________________________________________
14) HealthMonitor / KillSwitch
Rol: Seguridad operativa.
•	HealthMonitor
o	watch_connectivity(), watch_staleness(data_feed)
o	auto_reconnect(), alerting()
•	KillSwitch
o	trigger(reason) → cierra todo, desactiva estrategias, requiere intervención.
o	armed_state y cooldown_policy
________________________________________
Mapeo a tus módulos
•	Extract_data → DataFeed (+ BrokerAdapter)
•	Df_Creator → DataStore (frames/indicadores)
•	Market_logic → StrategyBase (+ StrategyRegistry)
•	Position_Creator → OrderManager (+ RiskManager para sizing y límites)
________________________________________
Flujo de ejecución (alto nivel)
1.	App.boot() → carga Config/Secrets, BrokerAdapter.connect(), DataFeed.prime_history().
2.	Bucle App.run() en cada tick/beat:
o	Scheduler verifica MarketHours.
o	DataFeed.poll() → DataStore.update_bar()/compute_features().
o	StrategyRegistry.iterate() → cada Strategy.on_bar() emite Signals.
o	Por cada Signal: RiskManager.check_signal() y position_sizing().
o	Si OK: OrderManager.signal_to_order() y route().
o	BrokerAdapter reporta fills → OrderManager.on_fill() → Portfolio.apply_fill() → RiskManager.register_fill().
o	RiskManager.check_account_limits()/check_symbol_limits()/check_exposure_after(); si viola → KillSwitch.trigger().
o	Metrics/Logger/AuditTrail registran todo.
3.	App.shutdown() ante parada manual, error crítico o KillSwitch.
________________________________________
Notas de diseño
•	Extensibilidad: nuevas estrategias heredan de StrategyBase, sin tocar núcleo.
•	Seguridad: SecretsManager, límites en RiskManager, KillSwitch.
•	Reusabilidad: BrokerAdapter desacopla MT5/IB; cambiar broker no rompe estrategias.
•	Testabilidad: Strategy.on_bar() usa StrategyContext y DataStore.snapshot() → fácil unit tests con datos sintéticos.
•	Observabilidad: AuditTrail y Metrics permiten post-mortem y control en vivo.

