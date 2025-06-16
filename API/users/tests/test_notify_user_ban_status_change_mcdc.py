"""
Testes para o método notify_user_ban_status_change seguindo o critério MC/DC
(Modified Condition/Decision Coverage)

Este arquivo contém:
1. Análise das decisões e condições do método
2. Tabelas verdade para decisões compostas
3. Identificação dos pares de independência
4. Casos de teste MC/DC
5. Execução e validação dos testes
"""

from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from users.models import UserProfile
from users.signals import notify_user_ban_status_change


# Configuração de banco SQLite para testes
TEST_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


@override_settings(DATABASES=TEST_DATABASES)
class NotifyUserBanStatusChangeMCDCTests(TestCase):
    """
    Testes de caixa branca para o método notify_user_ban_status_change
    aplicando o critério MC/DC (Modified Condition/Decision Coverage)
    
    ANÁLISE DO MÉTODO:
    ------------------
    
    def notify_user_ban_status_change(sender, instance, **kwargs):
        if not instance.pk:                                    # D1
            return
    
        try:
            previous = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            previous = None
    
        user = instance.user
    
        if previous:                                           # D2
            if previous.is_banned != instance.is_banned:       # D3
                if instance.is_banned:                         # D4
                    send_ban_notification_email.delay(user.email, user.first_name, user.last_name)
                else:
                    send_unban_notification_email.delay(user.email, user.first_name, user.last_name)

    
    IDENTIFICAÇÃO DAS DECISÕES E CONDIÇÕES:
    ----------------------------------------
    
    D1: if not instance.pk
        C1: instance.pk is None (ou falsy)
        
    D2: if previous
        C2: previous is not None
        
    D3: if previous.is_banned != instance.is_banned
        C3: previous.is_banned != instance.is_banned
        
    D4: if instance.is_banned
        C4: instance.is_banned is True
    
    
    TABELAS VERDADE (para decisões com uma condição):
    -------------------------------------------------
    
    D1: if not instance.pk
    | C1 (instance.pk) | not C1 | D1 | Ação         |
    |------------------|--------|----|--------------| 
    | False (None)     | True   | T  | return       |
    | True (exists)    | False  | F  | continua     |
    
    D2: if previous
    | C2 (previous) | D2 | Ação     |
    |---------------|----|---------| 
    | None          | F  | termina  |
    | not None      | T  | continua |
    
    D3: if previous.is_banned != instance.is_banned
    | C3 (previous.is_banned != instance.is_banned) | D3 | Ação     |
    |-----------------------------------------------|----|---------| 
    | False (são iguais)                            | F  | termina  |
    | True (são diferentes)                         | T  | continua |
    
    D4: if instance.is_banned
    | C4 (instance.is_banned) | D4 | Ação                    |
    |------------------------|----|-----------------------| 
    | False                  | F  | send_unban_notification |
    | True                   | T  | send_ban_notification   |
    
    
    PARES DE INDEPENDÊNCIA PARA MC/DC:
    ----------------------------------
    
    Para D1 (C1): 
    - Par 1: C1=T, D1=T vs C1=F, D1=F
    
    Para D2 (C2):
    - Par 2: C2=T, D2=T vs C2=F, D2=F
    
    Para D3 (C3):
    - Par 3: C3=T, D3=T vs C3=F, D3=F
    
    Para D4 (C4):
    - Par 4: C4=T, D4=T vs C4=F, D4=F
    
    
    CASOS DE TESTE MC/DC:
    ---------------------
    
    CT1: instance.pk = None
         - Testa D1 com C1=True, D1=True (return imediato)
         
    CT2: instance.pk = 1, previous = None (primeiro save)
         - Testa D1 com C1=False, D1=False
         - Testa D2 com C2=False, D2=False (termina)
         
    CT3: instance.pk = 1, previous exists, previous.is_banned = False, instance.is_banned = False
         - Testa D1 com C1=False, D1=False
         - Testa D2 com C2=True, D2=True
         - Testa D3 com C3=False, D3=False (termina)
         
    CT4: instance.pk = 1, previous exists, previous.is_banned = False, instance.is_banned = True
         - Testa D1 com C1=False, D1=False
         - Testa D2 com C2=True, D2=True
         - Testa D3 com C3=True, D3=True
         - Testa D4 com C4=True, D4=True (send_ban_notification)
         
    CT5: instance.pk = 1, previous exists, previous.is_banned = True, instance.is_banned = False
         - Testa D1 com C1=False, D1=False
         - Testa D2 com C2=True, D2=True
         - Testa D3 com C3=True, D3=True
         - Testa D4 com C4=False, D4=False (send_unban_notification)
    """

    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

    def test_ct1_instance_pk_none_early_return(self):
        """
        CT1: Testa D1 com C1=True (instance.pk = None)
        Resultado esperado: Return imediato, sem executar resto do código
        
        Cobertura MC/DC:
        - D1: C1=True, D1=True
        """
        print("\n=== CT1: instance.pk = None (early return) ===")
        
        # Criar uma instância sem pk (novo objeto)
        profile = UserProfile(user=self.user, is_banned=False)
        
        # Verificar que pk é None
        self.assertIsNone(profile.pk)
        
        # Chamar o método diretamente
        with patch('users.tasks.send_ban_notification_email.delay') as mock_ban:
            with patch('users.tasks.send_unban_notification_email.delay') as mock_unban:
                result = notify_user_ban_status_change(UserProfile, profile)
                
                # Verificar que retornou None (return imediato)
                self.assertIsNone(result)
                
                # Verificar que nenhuma notificação foi enviada
                mock_ban.assert_not_called()
                mock_unban.assert_not_called()
        
        print("✓ CT1 passou: Early return quando instance.pk é None")

    def test_ct2_instance_pk_exists_but_no_previous(self):
        """
        CT2: Testa D1 com C1=False e D2 com C2=False
        instance.pk existe mas previous = None (primeiro save)
        
        Cobertura MC/DC:
        - D1: C1=False, D1=False (continua execução)
        - D2: C2=False, D2=False (termina sem notificação)
        """
        print("\n=== CT2: instance.pk existe mas previous = None ===")
        
        # Criar profile salvo no banco
        profile = UserProfile.objects.create(user=self.user, is_banned=False)
        self.assertIsNotNone(profile.pk)
        
        # Simular que não existe previous (DoesNotExist)
        with patch.object(UserProfile.objects, 'get', side_effect=UserProfile.DoesNotExist):
            with patch('users.tasks.send_ban_notification_email.delay') as mock_ban:
                with patch('users.tasks.send_unban_notification_email.delay') as mock_unban:
                    notify_user_ban_status_change(UserProfile, profile)
                    
                    # Verificar que nenhuma notificação foi enviada
                    mock_ban.assert_not_called()
                    mock_unban.assert_not_called()
        
        print("✓ CT2 passou: Não envia notificação quando previous = None")

    def test_ct3_previous_exists_same_ban_status(self):
        """
        CT3: Testa D1=False, D2=True, D3=False
        previous existe e status de ban não mudou
        
        Cobertura MC/DC:
        - D1: C1=False, D1=False (continua)
        - D2: C2=True, D2=True (continua)
        - D3: C3=False, D3=False (termina sem notificação)
        """
        print("\n=== CT3: previous existe mas status de ban não mudou ===")
        
        # Criar profile com is_banned=False
        profile = UserProfile.objects.create(user=self.user, is_banned=False)
        
        # Simular previous com mesmo status
        previous_profile = UserProfile(user=self.user, is_banned=False)
        
        with patch.object(UserProfile.objects, 'get', return_value=previous_profile):
            with patch('users.tasks.send_ban_notification_email.delay') as mock_ban:
                with patch('users.tasks.send_unban_notification_email.delay') as mock_unban:
                    notify_user_ban_status_change(UserProfile, profile)
                    
                    # Verificar que nenhuma notificação foi enviada
                    mock_ban.assert_not_called()
                    mock_unban.assert_not_called()
        
        print("✓ CT3 passou: Não envia notificação quando status não mudou")

    def test_ct4_user_gets_banned(self):
        """
        CT4: Testa D1=False, D2=True, D3=True, D4=True
        Usuario foi banido (previous.is_banned=False, instance.is_banned=True)
        
        Cobertura MC/DC:
        - D1: C1=False, D1=False (continua)
        - D2: C2=True, D2=True (continua)
        - D3: C3=True, D3=True (status mudou, continua)
        - D4: C4=True, D4=True (foi banido, send_ban_notification)
        """
        print("\n=== CT4: Usuário foi banido ===")
        
        # Criar profile que será banido
        profile = UserProfile.objects.create(user=self.user, is_banned=True)
        
        # Simular previous não banido
        previous_profile = UserProfile(user=self.user, is_banned=False)
        
        with patch.object(UserProfile.objects, 'get', return_value=previous_profile):
            with patch('users.tasks.send_ban_notification_email.delay') as mock_ban:
                with patch('users.tasks.send_unban_notification_email.delay') as mock_unban:
                    notify_user_ban_status_change(UserProfile, profile)
                    
                    # Verificar que notificação de ban foi enviada
                    mock_ban.assert_called_once_with(
                        self.user.email, 
                        self.user.first_name, 
                        self.user.last_name
                    )
                    mock_unban.assert_not_called()
        
        print("✓ CT4 passou: Envia notificação de ban quando usuário é banido")

    def test_ct5_user_gets_unbanned(self):
        """
        CT5: Testa D1=False, D2=True, D3=True, D4=False
        Usuario foi desbanido (previous.is_banned=True, instance.is_banned=False)
        
        Cobertura MC/DC:
        - D1: C1=False, D1=False (continua)
        - D2: C2=True, D2=True (continua)
        - D3: C3=True, D3=True (status mudou, continua)
        - D4: C4=False, D4=False (foi desbanido, send_unban_notification)
        """
        print("\n=== CT5: Usuário foi desbanido ===")
        
        # Criar profile que será desbanido
        profile = UserProfile.objects.create(user=self.user, is_banned=False)
        
        # Simular previous banido
        previous_profile = UserProfile(user=self.user, is_banned=True)
        
        with patch.object(UserProfile.objects, 'get', return_value=previous_profile):
            with patch('users.tasks.send_ban_notification_email.delay') as mock_ban:
                with patch('users.tasks.send_unban_notification_email.delay') as mock_unban:
                    notify_user_ban_status_change(UserProfile, profile)
                    
                    # Verificar que notificação de unban foi enviada
                    mock_unban.assert_called_once_with(
                        self.user.email, 
                        self.user.first_name, 
                        self.user.last_name
                    )
                    mock_ban.assert_not_called()
        
        print("✓ CT5 passou: Envia notificação de unban quando usuário é desbanido")

    def test_mc_dc_coverage_summary(self):
        """
        Teste de verificação da cobertura MC/DC completa
        
        RESUMO DA COBERTURA MC/DC ALCANÇADA:
        ------------------------------------
        
        Decisão D1 (if not instance.pk):
        ✓ CT1: C1=True, D1=True
        ✓ CT2-CT5: C1=False, D1=False
        
        Decisão D2 (if previous):
        ✓ CT2: C2=False, D2=False  
        ✓ CT3-CT5: C2=True, D2=True
        
        Decisão D3 (if previous.is_banned != instance.is_banned):
        ✓ CT3: C3=False, D3=False
        ✓ CT4-CT5: C3=True, D3=True
        
        Decisão D4 (if instance.is_banned):
        ✓ CT4: C4=True, D4=True
        ✓ CT5: C4=False, D4=False
        
        TODAS AS CONDIÇÕES E DECISÕES FORAM TESTADAS COM MC/DC!
        """
        print("\n" + "="*60)
        print("RESUMO DA COBERTURA MC/DC")
        print("="*60)
        
        coverage_map = {
            'D1 (if not instance.pk)': {
                'C1=True, D1=True': 'CT1',
                'C1=False, D1=False': 'CT2-CT5'
            },
            'D2 (if previous)': {
                'C2=False, D2=False': 'CT2',
                'C2=True, D2=True': 'CT3-CT5'
            },
            'D3 (if previous.is_banned != instance.is_banned)': {
                'C3=False, D3=False': 'CT3',
                'C3=True, D3=True': 'CT4-CT5'
            },
            'D4 (if instance.is_banned)': {
                'C4=True, D4=True': 'CT4',
                'C4=False, D4=False': 'CT5'
            }
        }
        
        for decision, conditions in coverage_map.items():
            print(f"\n{decision}:")
            for condition, test_case in conditions.items():
                print(f"   {condition} -> {test_case}")
        
        print(f"\n{'='*60}")
        print("COBERTURA MC/DC COMPLETA ALCANÇADA!")
        print("Todas as decisões e condições foram testadas!")
        print("Todos os pares de independência foram cobertos!")
        print("="*60)
        
        # Este teste sempre passa - é apenas informativo
        self.assertTrue(True)


@override_settings(DATABASES=TEST_DATABASES)
class IntegrationTests(TestCase):
    """
    Testes de integração para verificar o comportamento real do signal
    """
    
    def setUp(self):
        """Configuração inicial para os testes de integração"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            first_name='Integration',
            last_name='User'
        )

    @patch('users.tasks.send_ban_notification_email.delay')
    def test_real_ban_integration(self, mock_ban):
        """
        Teste de integração real: criar profile e banir via save()
        """
        print("\n=== TESTE INTEGRAÇÃO: Ban real via save() ===")
        
        # Criar profile inicial (não banido)
        profile = UserProfile.objects.create(user=self.user, is_banned=False)
        
        # Banir o usuário via save() - deve triggerar o signal
        profile.is_banned = True
        profile.save()
        
        # Verificar que a notificação foi enviada
        mock_ban.assert_called_once_with(
            self.user.email,
            self.user.first_name, 
            self.user.last_name
        )
        
        print("✓ Integração ban: Signal disparado corretamente no save()")

    @patch('users.tasks.send_unban_notification_email.delay')
    def test_real_unban_integration(self, mock_unban):
        """
        Teste de integração real: criar profile banido e desbanir via save()
        """
        print("\n=== TESTE INTEGRAÇÃO: Unban real via save() ===")
        
        # Criar profile inicial banido
        profile = UserProfile.objects.create(user=self.user, is_banned=True)
        
        # Desbanir o usuário via save() - deve triggerar o signal
        profile.is_banned = False
        profile.save()
        
        # Verificar que a notificação foi enviada
        mock_unban.assert_called_once_with(
            self.user.email,
            self.user.first_name, 
            self.user.last_name
        )
        
        print("✓ Integração unban: Signal disparado corretamente no save()")


if __name__ == '__main__':
    import unittest
    
    print("="*80)
    print("EXECUTANDO TESTES MC/DC PARA notify_user_ban_status_change")
    print("="*80)
    
    # Executar apenas os testes MC/DC
    suite = unittest.TestLoader().loadTestsFromTestCase(NotifyUserBanStatusChangeMCDCTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("EXECUTANDO TESTES DE INTEGRAÇÃO")
    print("="*80)
    
    # Executar testes de integração
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("TODOS OS TESTES CONCLUÍDOS!")
    print("="*80)
