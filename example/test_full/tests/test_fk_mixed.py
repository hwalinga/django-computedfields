# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from base import GenericModelTestBase, MODELS


class MixedForeignKeysAndBackDependenciesSimple(GenericModelTestBase):
    """
    Test cases for mixed simple foreign key and
    foreign key back relations (fk + fk_back, fk_back + fk).
    """
    def setUp(self):
        self.setDeps({
            # fk + fk_back
            'B': {'depends': ['f_ba.ag_f#name'],
                  'func': lambda self: self.name + ''.join(
                      MODELS['G'].objects.filter(f_ga=self.f_ba).values_list('name', flat=True))},
            # fk_back + fk
            'F': {'depends': ['fg_f.f_ga#name'],
                  'func': lambda self: self.name + ''.join(MODELS['A'].objects.filter(
                      pk__in=self.fg_f.all().values_list('f_ga', flat=True).distinct()
                  ).values_list('name', flat=True))},
        })
        self.a = self.models.A(name='a')
        self.a.save()
        self.b = self.models.B(name='b', f_ba=self.a)
        self.b.save()
        self.c = self.models.C(name='c', f_cb=self.b)
        self.c.save()
        self.d = self.models.D(name='d', f_dc=self.c)
        self.d.save()
        self.e = self.models.E(name='e', f_ed=self.d)
        self.e.save()
        self.f = self.models.F(name='f', f_fe=self.e)
        self.f.save()
        self.g = self.models.G(name='g', f_gf=self.f, f_ga=self.a)
        self.g.save()

    def tearDown(self):
        self.resetDeps()

    def test_fk_fkback_insert(self):
        # since g got saved later we need to reload from db
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bg')

    def test_fk_fkback_update(self):
        # since g got saved later we need to reload from db
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bg')
        new_g = self.models.G(name='G', f_gf=self.f, f_ga=self.a)
        new_g.save()
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bgG')

    def test_fkback_fk_insert(self):
        self.assertEqual(self.f.comp, 'fa')

    def test_fkback_fk_update(self):
        self.assertEqual(self.f.comp, 'fa')
        new_a = self.models.A(name='A')
        new_a.save()
        self.g.f_ga = new_a
        self.g.save()
        self.f.refresh_from_db()
        self.assertEqual(self.f.comp, 'fA')
        new_g = self.models.G(name='G', f_gf=self.f, f_ga=self.a)
        new_g.save()
        self.f.refresh_from_db()
        self.assertEqual(self.f.comp, 'faA')


class MixedForeignKeysAndBackDependenciesMultipleOne(GenericModelTestBase):
    """
    Test cases for more complex foreign key and foreign key back relations
    (fk + fk_back + fk + fk_back, fk_back + fk + fk_back + fk).
    """
    def setUp(self):
        self.setDeps({
            # fk + fk_back + fk + fk_back
            'B': {'depends': ['f_ba.ag_f.f_gf.fd_f#name'],
                  'func': lambda self: self.name + ''.join(MODELS['D'].objects.filter(
                      f_df__in=MODELS['G'].objects.filter(f_ga=self.f_ba).values_list('f_gf', flat=True)
                  ).values_list('name', flat=True))},
            # fk_back + fk + fk_back + fk
            'D': {'depends': ['f_df.fg_f.f_ga.ab_f#name'],
                  'func': lambda self: ''}
        })
        self.a = self.models.A(name='a')
        self.a.save()
        self.b = self.models.B(name='b', f_ba=self.a)
        self.b.save()
        self.c = self.models.C(name='c', f_cb=self.b)
        self.c.save()
        self.d = self.models.D(name='d', f_dc=self.c)
        self.d.save()
        self.e = self.models.E(name='e', f_ed=self.d)
        self.e.save()
        self.f = self.models.F(name='f', f_fe=self.e)
        self.f.save()
        self.g = self.models.G(name='g', f_gf=self.f, f_ga=self.a)
        self.g.save()
        self.d.f_df = self.f
        self.d.save()

    def tearDown(self):
        self.resetDeps()

    def test_B_insert(self):
        # since g got saved later we need to reload from db
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bd')

    def test_B_update(self):
        # dep is D -> (F) -> G -> A -> B
        # change D
        self.d.name = 'D'
        self.d.save()
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bD')
        # new D
        new_d = self.models.D(name='d2', f_df=self.f)
        new_d.save()
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bDd2')
        # change b to different a
        new_a = self.models.A(name='newA')
        new_a.save()
        self.b.f_ba = new_a
        self.b.save()
        self.assertEqual(self.b.comp, 'b')
        # insert g with points to new a and old f
        # should restore old value in comp
        new_g = self.models.G(name='g', f_gf=self.f, f_ga=new_a)
        new_g.save()
        self.b.refresh_from_db()
        self.assertEqual(self.b.comp, 'bDd2')


class MixedForeignKeysAndBackDependenciesMultipleTwo(GenericModelTestBase):
    """
    Test cases for long path mixed foreign key and foreign key back relations
    (fk + fk + fk_back + fk_back, fk_back + fk_back + fk + fk).
    """
    def setUp(self):
        self.setDeps({
            # fk + fk + fk_back + fk_back
            # fk_back + fk_back + fk + fk
        })
        self.a = self.models.A(name='a')
        self.a.save()
        self.b = self.models.B(name='b', f_ba=self.a)
        self.b.save()
        self.c = self.models.C(name='c', f_cb=self.b)
        self.c.save()
        self.d = self.models.D(name='d', f_dc=self.c)
        self.d.save()
        self.e = self.models.E(name='e', f_ed=self.d)
        self.e.save()
        self.f = self.models.F(name='f', f_fe=self.e)
        self.f.save()
        self.g = self.models.G(name='g', f_gf=self.f, f_ga=self.a)
        self.g.save()
        self.d.f_df = self.f
        self.d.save()

    def tearDown(self):
        self.resetDeps()




